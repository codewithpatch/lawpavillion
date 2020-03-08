#   Law Pavillion Spider

## Description
Scraping judgment article details from http://lawpavilionplus.com/ and store it in MongoDB database.


## Setup Environment Variables
In `settings.py` add the following configuration:
1. Database connection
    ```
    USERNAME = urllib.parse.quote_plus(USERNAME)
    PASSWORD = urllib.parse.quote_plus(PASSWORD)
    MONGO_URI = URI.format(USERNAME, PASSWORD)
    ```
2. Database pipeline
    ```
    ITEM_PIPELINES = {
        'lawpavillion.pipelines.LawpavillionPipeline': 300,
    }
    ```



## Dependencies
1. Install the following dependencies from requirements.txt
    `pip install -r requirements.txt`
    
    ```buildoutcfg
    pymongo
    shub
    titlecase
    python-slugify
    docker-py
    ```

## Create eggfile
1. Create `setup.py` file at the same level as `scrapy.cfg` file with content as:
    ```
    from setuptools import setup, find_packages
    setup(
        name='housfy',
        version='1.0',
        packages=find_packages(),
        install_requires=[
            'pymongo',
            'shub',
            'titlecase',
            'python-slugify',
            'docker-py',
        ],
        entry_points = {'scrapy': ['settings = lawpavillion.settings']},
    )
    ```
    
2. Execute `python setup.py bdist_egg` in folder at the same level as `scrapy.cfg` file
3. Upload the eggfile into the scrapyd server using: `curl http://localhost:6800/addversion.json -F project=lawpvillion -F version=1.0 -F egg=@dist/lawpavillion-1.0-py3.7.egg`