import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import SantaItem
from itemloaders.processors import TakeFirst
import json
pattern = r'(\xa0)?'

class SantaSpider(scrapy.Spider):
	name = 'santa'
	base = 'https://www.santander.com/content/santander-corporate/san-global/en/sala-de-comunicacion/notas-de-prensa/jcr:content/root/responsivegrid/filterable_presearch.predefinedSearch.json?curr_lang=en&page={}'
	page = 1
	start_urls = [base.format(page)]

	def parse(self, response):
		data = json.loads(response.text)
		for index in range(len(data['results']['results'])):
			link = data['results']['results'][index]['path']
			date = data['results']['results'][index]['dateDocument']
			title = data['results']['results'][index]['name']
			extensions = ['pdf', 'PDF']
			if not any(file in link for file in extensions):
				yield response.follow(link, self.parse_post, cb_kwargs=dict(date=date, title=title))

		if not data['results']['isLastPage']:
			self.page += 1
			yield response.follow(self.base.format(self.page), self.parse)

	def parse_post(self, response, date, title):
		content = response.xpath('(//div[@class="row   py- "]//div[@class="aem-Grid aem-Grid--12 aem-Grid--default--12 "])[last()]//text()[not (ancestor::script)]').getall()
		content = [p.strip() for p in content if p.strip()]
		content = re.sub(pattern, "",' '.join(content))

		item = ItemLoader(item=SantaItem(), response=response)
		item.default_output_processor = TakeFirst()

		item.add_value('title', title)
		item.add_value('link', response.url)
		item.add_value('content', content)
		item.add_value('date', date)

		yield item.load_item()
