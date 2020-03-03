# -*- coding: utf-8 -*-
import urllib.parse

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
USERNAME = urllib.parse.quote_plus('chester')
PASSWORD = urllib.parse.quote_plus('aFLUKxoBMau9MNX7')

MONGO_URI = 'mongodb+srv://{}:{}@cluster0-jz9uu.mongodb.net/test?retryWrites=true&w=majority'.format(USERNAME, PASSWORD)
MONGO_DATABASE = 'law_pavillion'
MONGODB_COLLECTION = 'sc_judgment'

# LOG_ENABLED = True
# LOG_FILE = 'scrapy.log'
# LOG_ENCODING = True
