# -*- coding: utf-8 -*-

import json
import scrapy


class ExchangeSpider(scrapy.Spider):
    """
        scrapy crawl exchange_rate -o data/exchange.json
    """

    name = 'exchange_rate'
    start_urls = [
        'https://www.cbr-xml-daily.ru/daily_json.js',
    ]

    def parse(self, response):
        yield json.loads(response.body)
