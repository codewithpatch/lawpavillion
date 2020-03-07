# -*- coding: utf-8 -*-

import pymongo
from scrapy.utils.project import get_project_settings


class LawpavillionPipeline(object):
    collection_name = 'sc_judgment'
    settings = get_project_settings()
    CRAWL_PAGINATION = settings.get('CRAWL_PAGINATION')
    TEST_MODE = settings.get('TEST_MODE')

    def __init__(self, mongo_uri, mongo_db, spider_name):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.spider_name = spider_name

        if spider_name == 'sc_spider':
            self.collection_name = 'sc_judgment'
        elif spider_name == 'ca_spider':
            self.collection_name = 'ca_judgment'

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items'),
            spider_name=crawler.spider.name
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri, authSource='admin')
        pymongo.MongoClient()
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.db[self.collection_name].insert_one(dict(item))
        return item


class TestPipeline(object):
    def process_item(self, item, spider):
        return item
