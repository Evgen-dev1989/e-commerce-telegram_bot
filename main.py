import asyncio

import asyncpg
import requests
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from lxml import html
from lxml.html import HtmlElement

from config import database, host, password, port, token, user

url = 'https://www.omegawatches.com/en-au/suggestions/omega-mens-watches'

import time

import requests
from lxml import html

create_db = (
    """
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL,
            time TIMESTAMP DEFAULT NOW(),
            user_id INTEGER PRIMARY KEY NOT NULL,
            user_name VARCHAR(250) NOT NULL,
            first_name VARCHAR(250),
            last_name VARCHAR(250)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS categories (
            user_id INTEGER,
            category VARCHAR(100),
            time TIMESTAMP DEFAULT NOW(),
            FOREIGN KEY (user_id )
            REFERENCES users (user_id )
            ON UPDATE CASCADE
            ON DELETE CASCADE
)
    """
)

async def connect_db():

    return await asyncpg.connect(user=user, password=password, database=database, host=host, port=port)



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

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="button 1"), KeyboardButton(text="button 2")],
        [KeyboardButton(text="button 3")]
    ],
    resize_keyboard=True
)


async def keyboard_handler(message: types.Message):
    await message.answer("Select an option:", reply_markup=keyboard)



async def main():
    start = time.perf_counter()
    conn = await connect_db()

    bot = Bot(token=token)
    dp = Dispatcher()

    watches = await get_watches(url)
    #print(f"quantity: {len(watches)}")

    await conn.execute(*create_db)
    dp.message.register(start_handler, Command("start"))
    dp.message.register(keyboard_handler)
 

    end = time.perf_counter()
    print(f"execution time: {end - start:.6f} seconds")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())