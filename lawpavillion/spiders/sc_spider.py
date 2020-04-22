# -*- coding: utf-8 -*-
import logging
import re
import socket
import uuid
import posixpath
from datetime import datetime
from titlecase import titlecase

import scrapy
from slugify import slugify
from inline_requests import inline_requests
from urllib.parse import urljoin

from lawpavillion.items import LawpavillionItem


class JudgmentSpiderSpider(scrapy.Spider):
    name = 'sc_spider'
    CRAWL_PAGINATION = True     # True if prod
    GET_ONE_URL = False         # False if prod
    CRAWL_PAGE_URL = False      # False if prod
    TEST_MODE = False           # False if prod

    def __init__(
            self,
            page_url='https://lawpavilionplus.com/summary/judgments/?suitno=SC.32%2F1994&from'
                     '=OPJ6MhzKBqrbgLdDrWvaYoghN%2B2HQ5abLqooqBwT1fg%3D',
            url_file=None,
            *args,
            **kwargs
    ):

        self.base_url = 'https://lawpavilionplus.com/'
        self.login_url = 'https://lawpavilionplus.com/?fresh=1'
        self.start_urls = [self.login_url]
        self.page_url = page_url

        if not page_url and url_file is None:
            TypeError('No page URL or URL file passed.')

        if url_file is not None:
            with open(url_file, 'r') as f:
                self.start_urls = f.readlines()
        # if page_url:
        #     # Replaces the list of URLs if url_file is also provided
        #     self.start_urls = [page_url]

        super().__init__(*args, **kwargs)

    def parse(self, response):
        logging.info('THIS IS YOUR SOCKETHOSTNAME: {}'.format(socket.gethostname()))
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
        if self.GET_ONE_URL:
            judgement_url_list = [judgement_url_list[0]]
        if self.CRAWL_PAGE_URL:
            judgement_url_list = [self.page_url]

        for url in judgement_url_list:
            yield scrapy.Request(url, callback=self.crawl_initial_page)

        next_page = response.xpath('//li[@class="next"]//@href').get()
        if next_page and self.CRAWL_PAGINATION:
            next_page = urljoin(self.base_url, next_page)
            yield scrapy.Request(url=next_page, callback=self.parse_judgement_url)

    @inline_requests
    def crawl_initial_page(self, response):
        item = LawpavillionItem()

        relative_judgement_url = response.css('#pagecontent .btn-primary::attr(href)').get()
        full_judgement_url = urljoin(self.base_url, relative_judgement_url)
        fj_response = yield scrapy.Request(full_judgement_url)

        # resource
        uid = uuid.uuid4().hex[:5]
        cite = self.get_name_abbrv(response)
        name_abbreviation = self.get_name_abbrv(response)
        name_abbreviation = name_abbreviation.strip() if name_abbreviation else None
        name = response.css('h3.casetitle.red::text').get().replace('  ', ' ')
        name = titlecase(name.lower())
        slug = slugify(name_abbreviation) if name_abbreviation else slugify(name)

        item['id'] = uid
        item['url'] = 'https://api.firmtext.com/cases/{}/'.format(uid)
        item['name'] = name
        item['name_abbreviation'] = name_abbreviation if name_abbreviation else name
        item['slug'] = slug
        item['suit_no'] = response.css('h3.casetitle::text').re_first('SC.+')
        decision_date = self.get_decision_date(response)
        item['decision_date'] = decision_date

        # citations list
        item['citations'] = self.get_citations(response, cite, decision_date, uid)

        # court
        court_details = self.get_court_details(response)
        item['court'] = court_details

        # jurisdiction
        jurisdiction_details = self.get_jurisdiction_details()
        item['jurisdiction'] = jurisdiction_details

        # frontend
        frontend = self.generate_frontend(court_details, jurisdiction_details, uid, slug)
        item['frontend'] = frontend

        # casebody
        ratio_decidendi = self.get_ratio_decidendi(fj_response)
        opinions = self.get_opinion(fj_response)
        judges = self.get_judges(response)
        appellants = self.get_names(response, 'Appellant')
        respondents = self.get_names(response, 'Respondent')
        attorneys = self.get_attorneys(fj_response)
        summary = response.css('summary::text').get()

        item['casebody'] = {
            'ratio_decidendi': ratio_decidendi,
            'opinions': opinions,
            'judges': judges,
            'appellants': appellants,
            'respondents': respondents,
            'attorneys': attorneys,
            'summary': summary,
        }

        appellant_attorney = attorneys[0]['appellant']
        respondent_attoeney = attorneys[1]['respondent']

        item['attorneys'] = self.consolidate_attorney_names(appellant_attorney, respondent_attoeney)

        yield item

    def get_name_abbrv(self, response):
        citation = response.css('.green+ p::text').re_first('.+')
        if citation == '; ; ':
            return None

        if citation:
            try:
                return_string = re.search('(.+)\s\(\d{4}', citation).group(1)
                return return_string
            except AttributeError:
                try:
                    return_string = re.search('(.+)\s?\(\d{4}', citation).group(1)
                    return return_string
                except AttributeError:
                    try:
                        return_string = re.search('(.+)\s?\[\d{4}', citation).group(1)
                        return return_string
                    except AttributeError:
                        return None

        else:
            return None

    def get_decision_date(self, response):
        raw_date = response.css('.date::text').re_first(', the (.+)')
        try:
            date_in_list = re.search('(\d+)\w+ day of (\w+), (\d{4})', raw_date).groups()
        except:
            return ''

        strdate = ' '.join(date_in_list)
        oldformat = datetime.strptime(strdate, '%d %B %Y')

        return {
            'year': oldformat.strftime('%Y'),
            'month': oldformat.strftime('%m'),
            'date': oldformat.strftime('%d'),
        }

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

    def get_citations(self, response, cite, decision_date, uid):
        citation_list = []
        citation_raw_list = response.css('.green+ p::text')

        for citation in citation_raw_list:
            type = citation.re_first('\d{4}\)[^A-Za-z]+(\w+\.?\w+?)')
            full_citation = citation.re_first('.+')
            if cite == '; ; ':
                cite = ''
            name = ''

            if type == 'NWLR':
                name = 'Nigerian Weekly Law Reports'
            elif type == 'FTLR':
                name = 'Firmtext Law Reports'
            elif not cite:
                # logging.warning('No typed were parsed in getting the citations. Check get_citations method...')
                return ''

            citation_list.append({
                'type': type,
                'name': name,
                'cite': full_citation,
            })

            if not cite:
                break

            # "${name_abbreviation} (${decision_date.year}) FTLR ${uuid}"
            citation_list.append({
                'type': 'FTLR',
                'name': 'Firmtext Law Reports',
                'cite': cite + " ({}) FTLR {}".format(decision_date['year'], uid)
            })

        return citation_list

    def get_ratio_decidendi(self, response):
        ratio_decidendi = []
        ratio_decidendi_list = response.css('.blue .ratio')

        for ratio in ratio_decidendi_list:
            number = int(ratio.css('::text').re_first('\d+'))
            matter = ratio.css('b span.red::text').re_first('(.+) -')
            topic = ratio.css('b span.green::text').re_first('(.+):')
            text = ratio.css('p.blue::text').re_first('"(.+)"')
            author = ratio.css('p.blue::text').re_first('PER (.+) \(')
            if not author:
                author = ratio.css('p.blue::text').re_first('Per (.+) \(')
            ref = ratio.css('p.blue::text').re_first('\((.+)\)')

            ratio_decidendi.append({
                'number': number,
                'matter': matter,
                'topic': topic,
                'text': text,
                'author': author,
                'ref': ref,
            })

        return ratio_decidendi

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

    def get_court_details(self, response):
        court_name = response.css('h4::text').re_first('In The (.+)')
        court_id = uuid.uuid4().hex[:5]

        if 'Supreme' in court_name:
            court_name_abbreviation = 'SCNG'
            court_url = 'https://api.firmtext.com/courts/scng/'
            court_slug = 'scng'
        elif 'Appeal' in court_name:
            court_name_abbreviation = 'ACNG'
            court_url = 'https://api.firmtext.com/courts/apng/'
            court_slug = 'apng'
        else:
            logging.WARNING("Court details isn't Supreme Court or Appeal Court. check get_court_details method")
            return None

        return {
            'name_abbreviation': court_name_abbreviation,
            'url': court_url,
            'slug': court_slug,
            'id': court_id,
            'name': court_name
        }

    def get_jurisdiction_details(self):
        url = 'https://api.firmtext.com/jurisdictions/ng/'
        slug = 'ng'
        whitelisted = 'false'
        jurisdiction_id = 39
        name_long = 'Nigeria'
        name = 'NG'

        return {
            'url': url,
            'slug': slug,
            'whitelisted': whitelisted,
            'id': jurisdiction_id,
            'name_long': name_long,
            'name': name,
        }

    def generate_frontend(self, court_details, jurisdiction_details, uid, slug):
        # https://firmtext/cases/${jurisdiction.slug}/${court.slug}/${slug}-${uuid}/full
        # https://firmtext/cases/${jurisdiction.slug}/${court.slug}/${slug}-${uuid}
        base_url = 'https://firmtext/cases/'
        jurisdiction_slug = jurisdiction_details['slug']
        court_slug = court_details['slug']

        return {
            'full': posixpath.join(base_url, jurisdiction_slug, court_slug, slug, uid, 'full') + '/',
            'summary': posixpath.join(base_url, jurisdiction_slug, court_slug, slug, uid) + '/',
        }

    def consolidate_attorney_names(self, appellant_attorney, respondent_attoeney):
        attorneys = []
        for key, name in appellant_attorney:
            attorneys.append(name)
        for key, name in respondent_attoeney:
            attorneys.append(name)

        return attorneys