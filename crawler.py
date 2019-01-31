import scrapy

class Scraper(scrapy.Spider):
	name = "privacy_monitor"
	allowed_domains = ['addons.mozilla.org']
	start_urls = ['https://addons.mozilla.org/en-US/firefox/search/?sort=users']
	custom_settings = {
        'DOWNLOAD_DELAY': .5,
        'USER_AGENT': "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:64.0) Gecko/20100101 Firefox/64.0"
    }

	def parse(self, response):
		for item in response.css('.SearchResult'):
			# all URL's
			#response.css('.SearchResult').xpath('a/@href').extract()
			# first url
			#response.css('.SearchResult').xpath('a/@href').extract()

			##start here - all return as single item lists

			plugin_details['name'] = item.css('.SearchResult-name::text').extract()
			plugin_details['url'] = item.xpath('a/@href').extract()
			plugin_details['icon_url'] = item.css('.SearchResult-icon').xpath('@src').extract()
			plugin_details['users'] = item.css('.SearchResult-users-text::text').extract()
			request = scrapy.Request(plugin_details['url'],
                             callback=self.parse_page2)
			request.meta['details'] = plugin_details
			yield request

	def parse_plugin(self, response):
		plugin_details = response.meta['details']
		plugin_details['xpi_url'] = response.css('.AMInstallButton').xpath('a/@href').extract()
		yield plugin_details