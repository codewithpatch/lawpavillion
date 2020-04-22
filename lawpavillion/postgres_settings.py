# -*- coding: utf-8 -*-
import os

BOT_NAME = 'lawpavillion'

SPIDER_MODULES = ['lawpavillion.spiders']
NEWSPIDER_MODULE = 'lawpavillion.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

DOWNLOAD_DELAY = 5

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
             '(KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36 '

DATABASE = {
    'drivername': 'postgres',
    'host': os.environ.get('DB_HOST', '104.225.217.242'),
    'port': os.environ.get('DB_PORT', '5432'),
    'username': os.environ.get('DB_USERNAME', 'aw_scrape'),
    'password': os.environ.get('DB_PASSWORD', 'SPuK6RMcnny5sV'),
    'database': os.environ.get('DB_NAME', 'aw_scrape')
}

ITEM_PIPELINES = {
   'lawpavillion.pipelines.PostgresDBPipeline': 330
}
