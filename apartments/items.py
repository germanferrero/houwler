# -*- coding: utf-8 -*-
import re
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Join


class ApartmentGuideApartment(scrapy.Item):
    apartment_name = scrapy.Field()
    floor_name = scrapy.Field()
    address = scrapy.Field()
    state = scrapy.Field()
    city = scrapy.Field()
    phone = scrapy.Field()
    amenities = scrapy.Field()
    is_studio = scrapy.Field()
    beds = scrapy.Field()
    baths = scrapy.Field()
    square_feets = scrapy.Field()
    price = scrapy.Field()


def take_number(x):
    match = re.search('\d+\.*\d*', x)
    return match.group() if match else None


class ApartmentGuideItemLoader(ItemLoader):
    default_output_processor = TakeFirst()
    default_item_class = ApartmentGuideApartment

    baths_in = MapCompose(take_number)
    beds_in = MapCompose(take_number)
    square_feets_in = MapCompose(take_number)
    is_studio_in = MapCompose(lambda x: 'yes' if 'Studio' in x else 'no')
    price_in = MapCompose(lambda x: '-'.join(re.findall('\$\d+\.*\d*', x)))
    amenities_out = Join('-')
