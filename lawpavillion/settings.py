# -*- coding: utf-8 -*-
import urllib.parse
import socket

BOT_NAME = 'lawpavillion'

SPIDER_MODULES = ['lawpavillion.spiders']
NEWSPIDER_MODULE = 'lawpavillion.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

DOWNLOAD_DELAY = 5

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
             '(KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36 '

ITEM_PIPELINES = {
    'lawpavillion.pipelines.LawpavillionPipeline': 300,
    # 'lawpavillion.pipelines.TestPipeline': 300,
}

# dele@authoritywit.com
# Griffin003
if socket.gethostname() == 'BillionairesAir':
    USERNAME = urllib.parse.quote_plus('chester')
    PASSWORD = urllib.parse.quote_plus('C4Kz9D1iYxSIVn8g')
    MONGO_URI = 'mongodb+srv://{}:{}@cluster0-jz9uu.mongodb.net/test?retryWrites=true&w=majority'.format(USERNAME,
                                                                                                         PASSWORD)
else:
    # mongodb://[username:password@]host1[:port1]
    USERNAME = urllib.parse.quote_plus('firmbird')
    PASSWORD = urllib.parse.quote_plus('Qr2QCZeK')
    DATABASE = 'firmbird'
    MONGO_URI = 'mongodb://{}:{}@209.182.235.140:27017/{}?retryWrites=true&w=majority'.format(USERNAME,
                                                                                              PASSWORD,
                                                                                              DATABASE)

MONGO_DATABASE = 'law_pavillion'

CRAWL_PAGINATION = False
GET_ONE_URL = True
CRAWL_ONE_SECTION = True
CRAWL_PAGE_URL = False
TEST_MODE = True
