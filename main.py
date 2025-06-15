import asyncio

import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from lxml import html
from lxml.html import HtmlElement

from config import token

url = 'https://www.omegawatches.com/en-au/suggestions/omega-mens-watches'

import requests
from lxml import html
import time

def remove_duplicates(watches):
    unique = []
    seen = set()
    for w in watches:
        key = (w['name'], w['price'], w['characteristics'])
        if key not in seen:
            seen.add(key)
            unique.append(w)
    return unique

async def get_watches(url):
    response = requests.get(url)
    tree = html.fromstring(response.content)
    items = tree.xpath('//li[contains(@class, "product-item")]')
    watches = []
    for item in items:
        name = item.xpath('.//p[contains(@class, "collection")]/text()')
        price = item.xpath('.//span[@class="price"]/text()')
        characteristics = item.xpath('.//p[contains(@class, "name")]/text()')
        #print(f"Name: {name}, Price: {price}, Characteristics: {characteristics}")
        watches.append({
            'name': name[0].strip() if name else '',
            'price': price[0].strip() if price else '',
            'characteristics': characteristics[0].strip() if characteristics else ''
        })

    watches = remove_duplicates(watches)
    return watches




async def start_handler(message: types.Message):
    await message.answer("Welcome to the Omega Watches Bot! Type /watches to see the latest watches.")

async def main():
    start = time.perf_counter()
    bot = Bot(token=token)
    dp = Dispatcher()
    watches = await get_watches(url)
    print(f"quantity: {len(watches)}")
    dp.message.register(start_handler, Command("start"))
    end = time.perf_counter()
    print(f"execution time: {end - start:.6f} seconds")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())