# -*- coding: utf-8 -*-

import re
import json
import time

import scrapy
from scrapy.selector import Selector


class LMSearchSpider(scrapy.Spider):
    """
        scrapy crawl lm_search -a search="something" -o data/lmresult.jl
    """

    name = 'lm_search'

    def __init__(self, search=None, *args, **kwargs):
        super(LMSearchSpider, self).__init__(*args, **kwargs)

        self.n = None
        self.url_from = 0
        self.items_count = 40
        self.search = search
        self.session_id = int(time.time())

    def start_requests(self):
        url = f'https://www.livemaster.ru/search.php?vr=0&searchtype=1&search={self.search}&sectiontype=1'
        yield scrapy.Request(url, callback=self.parse_lm_html)

    def _json_request(self):
        url = f'https://www.livemaster.ru/search.php?searchtype=1&search={self.search}&thw=0&sectiontype=1&from={self.url_from}'

        return scrapy.Request(
                url,
                method='POST',
                headers={
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    },
                body=f'infinityScroll=true&itemsCount={self.items_count}',
                callback=self.parse_lm_json,
            )

    def parse_lm_json(self, response):
        """
        {'items': [
            {
                'price_parsed': '<span><span class="price" id="pr_645_32095095">645&nbsp;<span><span class="cr js-stat-main-items-money">руб</span></span></span></span>'
            }
        ]}
        """

        def convert_price(item):
            if 'price_parsed' in item:
                d = Selector(text=item['price_parsed']).xpath('//span/text()').get()
                r = re.findall(r'[\.0-9]+', d)
                if r:
                    return float(''.join(r))
            return None

        self.n -= 40

        data = json.loads(response.body)
        if 'items' in data:
            for item in data['items']:
                item['search_str'] = self.search
                item['scrapy_session_id'] = self.session_id
                item['price'] = convert_price(item)
                yield item

        if self.n > 0:
            self.url_from += 40
            yield self._json_request()

    def parse_lm_html(self, response):
        # По Вашему запросу найдено 3 047 работ
        c = response.xpath('//span[contains(@class, "catalog__content-under-title")]/text()').get()
        r = re.findall(r'[0-9]+', c)
        self.n = int(''.join(r))

        if self.n and self.n > 0:
            yield self._json_request()
