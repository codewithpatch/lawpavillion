# -*- coding: utf-8 -*-
import logging
import re
import uuid
import posixpath
from datetime import datetime
from titlecase import titlecase

import scrapy
from slugify import slugify
from inline_requests import inline_requests
from urllib.parse import urljoin
from scrapy.utils.project import get_project_settings

from lawpavillion.items import RuleofCourtItem


class RuleofcourtSpiderSpider(scrapy.Spider):
    name = 'ruleofcourt_spider'
    settings = get_project_settings()
    CRAWL_PAGINATION = settings.get('CRAWL_PAGINATION')
    GET_ONE_URL = settings.get('GET_ONE_URL')
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
        rule_of_court_url = 'https://lawpavilionplus.com/RulesOfCourts/'
        yield scrapy.Request(url=rule_of_court_url, callback=self.get_view_order_urls)

    def get_view_order_urls(self, response):
        view_ruleorder_urls = response.css('.pull-right::attr(href)').getall()
        view_ruleorder_urls = list(map(lambda url: urljoin(self.base_url, url), view_ruleorder_urls))
        if self.GET_ONE_URL:
            view_ruleorder_urls = [view_ruleorder_urls[0]]
        if self.CRAWL_PAGE_URL:
            view_ruleorder_urls = [self.page_url]

        for ruleorder_url in view_ruleorder_urls:
            if '/rules/show/' in ruleorder_url:
                yield scrapy.Request(url=ruleorder_url, callback=self.parse_rules)
            else:
                yield scrapy.Request(url=ruleorder_url, callback=self.get_view_order_urls)

        next_page = response.xpath('//li[@class="next"]//@href').get()
        if next_page and self.CRAWL_PAGINATION:
            next_page = urljoin(self.base_url, next_page)
            yield scrapy.Request(url=next_page, callback=self.get_view_order_urls)

    def parse_rules(self, response):
        item = RuleofCourtItem()

        rules = response.css('.brown::text').getall()
        rule_numbers = self.transform_rule_title(rules, 'rule_number')
        rule_titles = self.transform_rule_title(rules, 'rule_title')
        rule_descriptions = response.css('.justify::text').getall()

        return item

    def transform_rule_title(self, rules, part):
        if part == 'rule_number':
            get_rule_number = lambda rule: re.search('(RULE \d+) -', rule).group(1)
            return list(map(get_rule_number, rules))
        elif part == 'rule_title':
            get_rule_title = lambda rule: re.search('- (.+)', rule).group(1)
            return list(map(get_rule_title, rules))
