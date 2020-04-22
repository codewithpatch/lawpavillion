# -*- coding: utf-8 -*-
import logging
import json
import socket

import pymongo
from scrapy.utils.project import get_project_settings

from sqlalchemy.orm import sessionmaker

from lawpavillion.models import (
    connect_db, create_schema, create_tables,
    Case, Court, Jurisdiction, Casebody, Attorney, Opinion, Judge, Ratio_decidendi
)


class LawpavillionPipeline(object):
    collection_name = 'sc_judgment'
    settings = get_project_settings()
    CRAWL_PAGINATION = settings.get('CRAWL_PAGINATION')
    TEST_MODE = settings.get('TEST_MODE')

    if socket.gethostname() == 'BillionairesAir':
        authSource = 'admin'  # dev
    else:
        authSource = 'firmbird'  # prod

    def __init__(self, mongo_uri, mongo_db, spider_name):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.spider_name = spider_name

        if spider_name == 'sc_spider':
            self.collection_name = 'sc_judgment'
        elif spider_name == 'ca_spider':
            self.collection_name = 'ca_judgment'
        elif spider_name == 'ruleofcourt_spider':
            self.collection_name = 'rules_of_court'
        elif spider_name == 'lfn_spider':
            self.collection_name = 'laws_of_the_federation'

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items'),
            spider_name=crawler.spider.name
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(
            self.mongo_uri,
            authSource='firmbird',
            socketTimeoutMS=60000,
            serverSelectionTimeoutMS=60000,
        )  # change when test mode
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


class PostgresDBPipeline(object):
    def __init__(self):
        engine = connect_db()
        create_schema(engine, "law_pavillion")
        create_tables("law_pavillion")
        self.session = sessionmaker(bind=engine)

    def process_item(self, item, spider):
        session = self.session()

        # Process Case
        try:
            # Create case object with basic fields
            case = Case(
                id=item['id'],
                url=item['url'],
                name=item['name'],
                name_abbreviation=item['name_abbreviation'],
                slug=item['slug'],
                suit_no=item['suit_no'],
                decision_date=item['decision_date'],
                frontend=item['frontend'],
                citations=item['citations'],
            )
            session.add(case)
            session.commit()
        except Exception as e:
            session.rollback()
            session.close()
            logging.error(e)
            return item

        # Process Jurisdiction
        try:
            # Check if jurisdiction already exsists
            jurisdiction = session.query(Jurisdiction).filter(
                Jurisdiction.name_long == item['jurisdiction']['name_long']
            ).filter(
                Jurisdiction.name == item['jurisdiction']['name']
            )
            if not jurisdiction:
                jurisdiction = Jurisdiction(
                    id=item['jurisdiction']['id'],
                    slug=item['jurisdiction']['slug'],
                    whitelisted=item['jurisdiction']['whitelisted'],
                    name_long=item['jurisdiction']['name_long'],
                    name=item['jurisdiction']['name'],
                )
                session.add(jurisdiction)
                session.commit()
        except Exception as e:
            session.rollback()
            session.close()
            logging.error(e)
            return item

        # Property Court
        try:
            # Check if court already exists
            court = session.query(Court).filter(
                Court.name == item['court']['name']
            ).filter(
                Court.name_abbreviation == item['court']['name_abbreviation']
            ).filter(
                Court.slug == item['court']['slug']
            ).filter(
                Court.id == item['court']['id']
            )
            if not court:
                court = Court(
                    name=item['court']['name'],
                    name_abbreviation=item['court']['name_abbreviation'],
                    slug=item['court']['slug'],
                    id=item['court']['id']
                )
                session.add(court)
                session.commit()
        except Exception as e:
            session.rollback()
            session.close()
            logging.error(e)
            return item

        # Process Casebody
        try:
            # Check if casebody already exists
            casebody = session.query(Casebody).filter(
                Casebody.summary == item['casebody']['summary']
            )
            if not casebody:
                casebody = Casebody(
                    id=item['casebody']['id'],
                    summary=item['casebody']['summary'],
                    respondents=item['casebody']['respondents'],
                )
                session.add(casebody)
                session.commit()

        except Exception as e:
            session.rollback()
            session.close()
            logging.error(e)
            return item

        # Process Attorney
        try:
            # Check if attorney already exsists
            for name in item['attorneys']:
                attorney = session.query(Attorney).filter(
                    Attorney.name == name
                )
                if not attorney:
                    attorney = Attorney(
                        name=name,
                        title='To setup'
                    )
                    session.add(attorney)
                    session.commit()

        except Exception as e:
            session.rollback()
            session.close()
            logging.error(e)
            return item

        # Process Opinion
        try:
            # Check if opinion already exists
            opinions = item['casebody'].get('opinions')
            if opinions:
                for opinion_hash in opinions:
                    opinion = session.query(Opinion).filter(
                        Opinion.author == opinion_hash['author']
                    ).filter(
                        Opinion.text == opinion_hash['text']
                    )
                    if not opinion:
                        opinion = Opinion(
                            author = opinion_hash['author'],
                            text = opinion_hash['text']
                        )
                        session.add(opinion)
                        session.commit()
        except Exception as e:
            session.rollback()
            session.close()
            logging.error(e)
            return item

        # Process Judge
        try:
            # Check if judge already exists
            judges = item['casebody'].get('judges')
            for judge_hash in judges:
                judge = session.query(Judge).filter(
                    Judge.name == judge_hash.get('name')
                ).filter(
                    Judge.title == judge_hash.get('title')
                )
                if not judge:
                    judge = Judge(
                        name=judge_hash.get('name'),
                        title=judge_hash.get('title')
                    )
                    session.add(judge)
                    session.commit()
        except Exception as e:
            session.rollback()
            session.close()
            logging.error(e)
            return item

        # Process Ratio decidendi
        try:
            # Check if ratio decidendi already exists
            ratio_decidendis = item['casebody'].get('ratio_decidendi')
            for decidendi_hash in ratio_decidendis:
                ratio_decidendi = session.query(Ratio_decidendi).filter(
                    Ratio_decidendi.matter == decidendi_hash.get('matter')
                ).filter(
                    Ratio_decidendi.topic == decidendi_hash.get('topic')
                ).filter(
                    Ratio_decidendi.text == decidendi_hash.get('text')
                )

                if not ratio_decidendi:
                    ratio_decidendi = Ratio_decidendi(
                        matter=decidendi_hash.get('matter'),
                        topic=decidendi_hash.get('topic'),
                        text=decidendi_hash.get('text')
                    )
        except Exception as e:
            session.rollback()
            session.close()
            logging.error(e)



