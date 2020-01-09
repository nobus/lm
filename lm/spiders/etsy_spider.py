# -*- coding: utf-8 -*-

import json
import time

import scrapy

from lm.settings import ETSY_API_KEY


class EtsySpider(scrapy.Spider):
    """
        scrapy crawl etsy -a keywords="something" -o data/etsy.jl
    """

    name = 'etsy'

    def __init__(self, keywords=None, *args, **kwargs):
        super(EtsySpider, self).__init__(*args, **kwargs)

        self.keywords = keywords
        self.session_id = int(time.time())
        self.offset = 0

    def _get_url(self):
        return f'https://openapi.etsy.com/v2/listings/active?keywords={self.keywords}&api_key={ETSY_API_KEY}&offset={self.offset}'

    def start_requests(self):
        url = self._get_url()
        yield scrapy.Request(url)

    def parse(self, response):
        data = json.loads(response.body)

        if 'results' in data:
            for params in data['results']:
                if 'listing_id' in params:
                    if 'price' in params:
                        params['price'] = float(params['price'])

                    if 'is_supply' in params:
                        if params['is_supply'] in ['true', 'True']:
                            params['is_supply'] = True
                        elif params['is_supply'] in ['false', 'False']:
                            params['is_supply'] = False
                        else:
                            params['is_supply'] = None

                params['scrapy_session_id'] = self.session_id
                params['keywords'] = self.keywords
                yield params

        self.offset = data['pagination']['next_offset']
        limit_rem = int(response.headers.get("X-RateLimit-Remaining", 0))

        if self.offset > 50000:
            raise scrapy.exceptions.CloseSpider(f'OFFSET too big {offset}, exit!')
        elif limit_rem <= 0:
            raise scrapy.exceptions.CloseSpider(f'Limit remaining {limit_rem}, exit!')
        else:
            url = self._get_url()
            yield scrapy.Request(url)
