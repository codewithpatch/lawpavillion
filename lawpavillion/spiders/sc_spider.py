# -*- coding: utf-8 -*-
import re
import uuid

import scrapy
from inline_requests import inline_requests
from urllib.parse import urljoin

from lawpavillion.items import LawpavillionItem


class JudgmentSpiderSpider(scrapy.Spider):
    name = 'sc_spider'
    CRAWL_PAGINATION = True
    TEST_MODE = False

    def __init__(self, page_url='', url_file=None, *args, **kwargs):
        self.base_url = 'https://lawpavilionplus.com/'
        self.login_url = 'https://lawpavilionplus.com/?fresh=1'
        self.start_urls = [self.login_url]

        if not page_url and url_file is None:
            TypeError('No page URL or URL file passed.')

        if url_file is not None:
            with open(url_file, 'r') as f:
                self.start_urls = f.readlines()
        if page_url:
            # Replaces the list of URLs if url_file is also provided
            self.start_urls = [page_url]

        super().__init__(*args, **kwargs)

    def parse(self, response):
        return scrapy.FormRequest.from_response(
            response,
            formdata={'LoginForm[username]': 'delomos@gmail.com', 'LoginForm[password]': 'bamidele003'},
            callback=self.after_login
        )

    def after_login(self, response):
        judgment_url = 'https://lawpavilionplus.com/sc/judgments/'
        yield scrapy.Request(url=judgment_url, callback=self.parse_judgement_url)

    def parse_judgement_url(self, response):
        relative_url_list = response.xpath('//li[@class="item-black clearfix"]//@href').getall()
        judgement_url_list = list(map(lambda url: urljoin(self.base_url, url), relative_url_list))
        if self.TEST_MODE:
            judgement_url_list = [judgement_url_list[0]]

        for url in judgement_url_list:
            yield scrapy.Request(url, callback=self.crawl_initial_page)

        next_page = urljoin(self.base_url, response.xpath('//li[@class="next"]//@href').get())
        if next_page and self.CRAWL_PAGINATION:
            yield scrapy.Request(url=next_page, callback=self.parse_judgement_url)

    @inline_requests
    def crawl_initial_page(self, response):
        item = LawpavillionItem()

        relative_judgement_url = response.css('#pagecontent .btn-primary::attr(href)').get()
        full_judgement_url = urljoin(self.base_url, relative_judgement_url)
        fj_response = yield scrapy.Request(full_judgement_url)

        # resource
        item['id'] = uuid.uuid4().hex[:5]
        item['url'] = response.url
        item['name'] = response.css('h3.casetitle.red::text').get()
        item['name_abbreviation'] = ''
        item['slug'] = ''
        item['decision_date'] = response.css('.date::text').re_first(', the (.+)')
        item['suite_no'] = response.css('h3.casetitle::text').re_first('SC.+')

        # citations list
        item['citations'] = self.get_citations(response)

        # court
        court_name_abbreviation = ''
        court_url = ''
        court_slug = ''
        court_id = ''
        court_name = response.css('h4::text').re_first('Supreme.+')
        item['court'] = {
            'name_abbreviation': court_name_abbreviation,
            'url': court_url,
            'slug': court_slug,
            'id': court_id,
            'name': court_name
        }

        # jurisdiction
        jurisdiction_url = ''
        jurisdiction_slug = ''
        jurisdiction_whitelisted = ''
        jurisdiction_id = ''
        jurisdiction_name_long = response.css('h4::text').re_first('Supreme.+of(.+)')
        jurisdiction_name = ''
        item['jurisdiction'] = {
            'url': jurisdiction_url,
            'slug': jurisdiction_slug,
            'whitelisted': jurisdiction_whitelisted,
            'id': jurisdiction_id,
            'name_long': jurisdiction_name_long,
            'name': jurisdiction_name,
        }

        # frontend
        frontend_full = ''
        frontend_summary = ''
        item['frontend'] = {
            'full': frontend_full,
            'summary': frontend_summary,
        }

        # casebody
        ratio_recidendi = self.get_ratio_recidendi(fj_response)
        opinions = self.get_opinion(fj_response)
        judges = self.get_judges(response)
        appellants = self.get_names(response, 'Appellant')
        respondents = self.get_names(response, 'Respondent')
        attorneys = self.get_attorneys(fj_response)
        summary = response.css('summary::text').get()

        item['casebody'] = {
            'ratio_recidendi': ratio_recidendi,
            'opinions': opinions,
            'judges': judges,
            'appellants': appellants,
            'respondents': respondents,
            'attorneys': attorneys,
            'summary': summary,
        }

        yield item

    def get_judges(self, response):
        judges = []
        names = response.css('.judges p::text').getall()
        titles = response.css('.judges span::text').getall()

        for name, title in zip(names, titles):
            judge = {
                'name': name,
                'title': title,
            }

            judges.append(judge)

        return judges

    def get_names(self, response, type):
        if type == 'Appellant':
            regex = 'h4+ .bold::text'
            to_remove = ' - Appellant(s)'
        elif type == 'Respondent':
            regex = '.bold+ .bold::text'
            to_remove = ' - Respondent(s)'

        name_list = []
        name_raw_list = response.css(regex).getall()

        for name in name_raw_list:
            name = re.sub('\d. ', '', name)
            name = name.replace(to_remove, '')

            name_list.append({'name': name})

        return name_list

    def get_citations(self, response):
        citation_list = []
        citation_raw_list = response.css('.green+ p::text')

        for citation in citation_raw_list:
            type = citation.re_first('\d{4}\)[^A-Za-z]+(\w+)')
            name = ''
            cite = citation.re_first('.+')

            citation_list.append({
                'type': type,
                'name': name,
                'cite': cite,
            })

        return citation_list

    def get_ratio_recidendi(self, response):
        ratio_recidendi = []
        ratio_recidendi_list = response.css('.blue .ratio')

        for ratio in ratio_recidendi_list:
            number = int(ratio.css('::text').re_first('\d+'))
            matter = ratio.css('b span.red::text').re_first('(.+) -')
            topic = ratio.css('b span.green::text').re_first('(.+):')
            text = ratio.css('p.blue::text').re_first('"(.+)"')
            author = ratio.css('p.blue::text').re_first('PER (.+) \(')
            if not author:
                author = ratio.css('p.blue::text').re_first('Per (.+) \(')
            ref = ratio.css('p.blue::text').re_first('\((.+)\)')

            ratio_recidendi.append({
                'number': number,
                'matter': matter,
                'topic': topic,
                'text': text,
                'author': author,
                'ref': ref,
            })

        return ratio_recidendi

    def get_opinion(self, response):
        opinion = []
        jsummary = response.xpath('//div[@class="jsummary"]//text()').re('\w.+\S')
        authors = response.css('.jsummary b::text').re('\w.+\S')[1:]
        authors = list(filter(lambda author: author[-1] == ':', authors))

        for index, author in enumerate(authors):
            current_author_index = jsummary.index(author)
            try:
                next_author = authors[index + 1]
                next_author_index = jsummary.index(next_author)
                opinion_in_list = jsummary[current_author_index + 1:next_author_index]
            except IndexError:
                opinion_in_list = jsummary[current_author_index + 1: -1]

            name = author.replace(':', '')
            text = '\n'.join(opinion_in_list)

            opinion.append({
                'author': name,
                'text': text,
            })

        return opinion

    def get_attorneys(self, response):
        all_attorney = response.css('.left')[2:]
        appellant_attorneys = self.names_to_list(all_attorney[0])
        respondent_attorneys = self.names_to_list(all_attorney[1])

        attorneys = [
            {
                'appellant': appellant_attorneys
            },
            {
                'respondent': respondent_attorneys
            }
        ]

        return attorneys

    def names_to_list(self, attorney_selector):
        name_hash_list = []

        attorney_names = attorney_selector.css('::text').getall()
        for name in attorney_names:
            name_hash_list.append({
                'name': name
            })

        return name_hash_list
