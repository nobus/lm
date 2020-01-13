# -*- coding: utf-8 -*-

import json
from collections import defaultdict

import scrapy

from lm.settings import VK_ACCESS_TOKEN


class VkAPI:
    def __init__(self, keywords):
        """
            https://vk.com/dev/search.getHints
            https://vk.com/dev/market.getAlbums
            https://vk.com/dev/market.get
            https://vk.com/dev/market.getCategories
        """
        self.keywords = keywords
        self.vk_api_ver='5.69'

        self.hints_limit = 200
        self.hints_offset = 0

        self.market_count = 200
        self.market_offset = defaultdict(int)

    def search_get_hints(self, callback):
        url = f'https://api.vk.com/method/search.getHints?q={self.keywords}&v={self.vk_api_ver}&limit={self.hints_limit}&offset={self.hints_offset}&search_global=1&access_token={VK_ACCESS_TOKEN}'
        self.hints_offset += self.hints_limit

        return scrapy.Request(url, callback=callback)

    def market_get(self, callback, owner_id):
        url = f'https://api.vk.com/method/market.get?owner_id={owner_id}&v={self.vk_api_ver}&count={self.market_count}&offset={self.market_offset[owner_id]}&access_token={VK_ACCESS_TOKEN}'
        self.market_offset[owner_id] += self.market_count

        return scrapy.Request(url, callback=callback)

class VKMarketSpider(scrapy.Spider):
    """
        scrapy crawl vkmarket -a keywords="something" -o data/vkmarket.jl
    """

    name = 'vkmarket'

    def __init__(self, keywords=None, *args, **kwargs):
        super(VKMarketSpider, self).__init__(*args, **kwargs)
        self.keywords = keywords

        self.vk = VkAPI(keywords)

    def start_requests(self):
        yield self.vk.search_get_hints(self.parse_hints)

    def parse_hints(self, response):
        data = json.loads(response.body)

        if 'response' in data and data['response']['count'] > 0:
            yield self.vk.search_get_hints(self.parse_hints)

            for item in data['response']['items']:
                item_type = item['type']
                owner_id = item[item_type]['id']

                if item_type == 'group':
                    owner_id = owner_id * -1
                    yield self.vk.market_get(self.parse_market_get, owner_id)
        else:
            raise scrapy.exceptions.CloseSpider(f'Data not found, exit!')

    def parse_market_get(self, response):
        data = json.loads(response.body)

        if 'response' in data:
            items = data['response']['items']

            if len(items) > 0:
                for item in items:
                    yield item

                yield self.vk.market_get(self.parse_market_get, item['owner_id'])
