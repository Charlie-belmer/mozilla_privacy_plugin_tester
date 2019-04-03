# -*- coding: utf-8 -*-
import scrapy


class MozillaAddonsSpider(scrapy.Spider):
    name = "privacy_monitor"
    allowed_domains = ['addons.mozilla.org']
    start_urls = ['https://addons.mozilla.org/en-US/firefox/search/?sort=users']
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'USER_AGENT': "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:64.0) Gecko/20100101 Firefox/66.0"
    }
    min_users = 1000

    def parse(self, response):
        smallest_count = 1000000
        for item in response.css('.SearchResult'):
            plugin_details = {}
            plugin_details['name'] = item.css('.SearchResult-name::text').extract()[0]
            plugin_details['url'] = item.xpath('a/@href').extract()[0]
            plugin_details['icon_url'] = item.css('.SearchResult-icon').xpath('@src').extract()[0]
            plugin_details['users'] = item.css('.SearchResult-users-text::text').extract()[0]
            user_count = int(plugin_details['users'][:plugin_details['users'].find(' ')].replace(',', ''))
            smallest_count = min(smallest_count, user_count)
            plugin_details['author'] = item.css('.SearchResult-author::text').extract()[0]
            url = response.urljoin(plugin_details['url'])
            request = scrapy.Request(url,
                             callback=self.parse_plugin)
            request.meta['details'] = plugin_details
            yield request

        print("--------------------------------------")
        print("- min user count found: " + str(smallest_count))
        print("- stopping at threshold: " + str(self.min_users))   
        print("--------------------------------------")
        if smallest_count > self.min_users:
            print(".....Opening next page........")
            next_page = response.css('.Paginate-item--next').xpath('@href').extract()[0]
            print(next_page)
            yield response.follow(next_page, self.parse)

    def parse_plugin(self, response):
        plugin_details = response.meta['details']
        plugin_details['xpi_url'] = response.css('.AMInstallButton').xpath('a/@href').extract()[0]
        plugin_details['version'] = response.css(".AddonMoreInfo-version::text").extract()[0]
        d = response.css(".AddonMoreInfo-last-updated::text").extract()[0]
        plugin_details['last_updated'] = d[d.find( '(' ) + 1:d.find( ')' )]

        yield plugin_details

