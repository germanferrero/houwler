import re
from urllib import urlencode
from urlparse import urlparse
from scrapy.spiders import Spider
# from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request
from apartments.items import ApartmentGuideFloorItemLoader


class ApartmentguideSpider(Spider):
    """This spider crawls apartments information from aparmentguide.com"""
    name = "apartmentguide"
    allowed_domains = ["apartmentguide.com"]
    # start_url contains links to all states.
    start_urls = ["http://www.apartmentguide.com/apartments"]

    browselinks_extractor = LinkExtractor(
        restrict_xpaths="//div[contains(@class,'browse_links')]")
    apartmentlinks_extractor = LinkExtractor(
        restrict_xpaths="id('resultWrapper')//a[contains(@class,'listing_title_links')]")

    def parse(self, response):
        """ Follow links to all states."""
        links = self.browselinks_extractor.extract_links(response)
        for link in links:
            meta = {'state_name': re.search(
                "(?P<state_name>.+) Apartments", link.text).group('state_name')}
            yield Request(url=link.url, meta=meta, callback=self.parse_state)

    def parse_state(self, response):
        """ Follow links to all cities."""
        links = self.browselinks_extractor.extract_links(response)
        for link in links:
            meta = response.meta
            meta['city_name'] = re.search(
                "(?P<city_name>.+) Apartments", link.text).group('city_name')
            params = urlencode({'sort': 'distance'})
            yield Request(url=link.url + '?{}'.format(params), meta=meta, callback=self.parse_city)

    def parse_city(self, response):
        """ Follow links to all apartments"""
        links = self.apartmentlinks_extractor.extract_links(response)
        city_links = [l for l in links if re.search(urlparse(response.url).path, l.url)]
        for link in city_links:
            yield Request(url=link.url, meta=response.meta, callback=self.parse_apartment)

        if len(city_links) == len(links):
            next_page = response.xpath("//a[contains(@class,'pagination-next')]/@href").extract_first()
            if next_page:
                yield Request(url=response.urljoin(next_page), meta=response.meta, callback=self.parse_city)

    def parse_apartment(self, response):
        apartment_name = response.xpath("//h1[contains(@class," +
                                        "'gallery-info-description-title')]/text()").extract_first()
        address = response.xpath("//li[contains(@class," +
                                 "'gallery-info-description-address')]//text()").extract_first()
        phone = response.xpath(
            "//span[contains(@class,'non_sem_number')]/text()").extract_first()
        amenities = response.xpath(
            "//li[contains(@class,'amenity-item')]/text()").extract()
        floors = response.xpath(
            "//div[contains(@class,'pdp-floorplan-list-result ')]")
        state = response.meta.get('state_name')
        city = response.meta.get('city_name')
        for floor in floors:
            loader = ApartmentGuideFloorItemLoader(selector=floor)
            loader.add_value('apartment_name', apartment_name)
            loader.add_value('address', address)
            loader.add_value('state', state)
            loader.add_value('city', city)
            loader.add_value('phone', phone)
            loader.add_value('amenities', amenities)
            loader.add_xpath(
                'floor_name', ".//span[contains(@class,'title')]/text()")
            loader.add_xpath(
                'beds', ".//div[contains(@class,'bed-container')]/text()")
            loader.add_xpath(
                'is_studio', ".//div[contains(@class,'bed-container')]/text()")
            loader.add_xpath(
                'baths', ".//div[contains(@class,'bath-container')]/text()")
            loader.add_xpath(
                'square_feets', ".//div[contains(@class,'sqft-container')]/text()")
            loader.add_xpath(
                'price', ".//div[contains(@class,'rent')]//text()")
            yield loader.load_item()
