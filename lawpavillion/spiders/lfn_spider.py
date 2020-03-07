# -*- coding: utf-8 -*-
from urllib.parse import urljoin

import scrapy
from scrapy.utils.project import get_project_settings

from lawpavillion.items import LawofFederationItem


class LfnSpiderSpider(scrapy.Spider):
    name = 'lfn_spider'
    settings = get_project_settings()
    CRAWL_PAGINATION = settings.get('CRAWL_PAGINATION')
    GET_ONE_URL = settings.get('GET_ONE_URL')
    CRAWL_ONE_SECTION = settings.get('CRAWL_ONE_SECTION')
    CRAWL_PAGE_URL = settings.get('CRAWL_PAGE_URL')
    TEST_MODE = settings.get('TEST_MODE')

    if TEST_MODE:
        custom_settings = {
            'ITEM_PIPELINES': {
                'lawpavillion.pipelines.TestPipeline': 300,
            }
        }

    def __init__(
            self,
            page_url="https://lawpavilionplus.com/summary/judgments/?suitno=CA%2FEK%2F51%2F2016&from"
                     "=USKHcECdWO9udpAEBWfLH3hhp2O1jV6LGl1RfMbHBEo%3D",
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

        super().__init__(*args, **kwargs)

    def parse(self, response):
        return scrapy.FormRequest.from_response(
            response,
            formdata={'LoginForm[username]': 'delomos@gmail.com', 'LoginForm[password]': 'bamidele003'},
            callback=self.after_login
        )

    def after_login(self, response):
        law_of_federation_url = 'https://lawpavilionplus.com/lfn/'
        yield scrapy.Request(url=law_of_federation_url, callback=self.get_laws_of_federation_urls)

    def get_laws_of_federation_urls(self, response):
        law_of_federation_urls = response.css('.table-striped a::attr(href)').getall()
        law_of_federation_urls = list(map(lambda url: urljoin(self.base_url, url), law_of_federation_urls))
        if self.GET_ONE_URL:
            law_of_federation_urls = [law_of_federation_urls[0]]
        if self.CRAWL_PAGE_URL:
            law_of_federation_urls = [self.page_url]

        for law_url in law_of_federation_urls:
            yield scrapy.Request(url=law_url, callback=self.view_section)

        next_page = response.xpath('//li[@class="next"]//@href').get()
        if next_page and self.CRAWL_PAGINATION:
            next_page = urljoin(self.base_url, next_page)
            yield scrapy.Request(url=next_page, callback=self.get_laws_of_federation_urls)

    def view_section(self, response):
        section_urls = response.css('.badge-info::attr(href)').getall()
        section_urls = list(map(lambda url: urljoin(self.base_url, url), section_urls))
        if self.CRAWL_ONE_SECTION:
            section_urls = [section_urls[0]]

        for section in section_urls:
            yield scrapy.Request(url=section, callback=self.parse_section)

    def parse_section(self, response):
        item = LawofFederationItem()

        section_title = response.css('h4::text').get()
        subsections = response.css('.span2::text').getall()
        subsection_description = response.css('.blue td::text').getall()

        return item
