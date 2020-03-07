# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.utils.project import get_project_settings

settings = get_project_settings()
TEST_MODE = settings.get('TEST_MODE')


class LawpavillionItem(scrapy.Item):
    if TEST_MODE:
        source = scrapy.Field()

    # resource
    id = scrapy.Field()  # none yet
    url = scrapy.Field()
    name = scrapy.Field()
    name_abbreviation = scrapy.Field()  # none yet
    slug = scrapy.Field()  # none yet
    decision_date = scrapy.Field()
    suit_no = scrapy.Field()

    # citations list
    citations = scrapy.Field()

    # court
    court = scrapy.Field()  # none yet

    # jurisdiction
    jurisdiction = scrapy.Field()  # none yet

    # frontend
    frontend = scrapy.Field()

    # casebody
    casebody = scrapy.Field()


class RuleofCourtItem(scrapy.Item):
    if TEST_MODE:
        source = scrapy.Field()


class LawofFederationItem(scrapy.Item):
    if TEST_MODE:
        source = scrapy.Field()


