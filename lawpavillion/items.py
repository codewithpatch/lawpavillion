# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class LawpavillionItem(scrapy.Item):
    # resource
    id = scrapy.Field()  # none yet
    url = scrapy.Field()
    name = scrapy.Field()
    name_abbreviation = scrapy.Field()  # none yet
    slug = scrapy.Field()  # none yet
    decision_date = scrapy.Field()
    suite_no = scrapy.Field()

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



