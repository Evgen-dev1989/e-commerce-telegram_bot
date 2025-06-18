import asyncio

import asyncpg
import requests
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from lxml import html
from lxml.html import HtmlElement

from config import database, host, password, port, token, user

url = 'https://www.omegawatches.com/en-au/suggestions/omega-mens-watches'

import time
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import types
import requests
from lxml import html

create_db = (
    """
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL,
        time TIMESTAMP DEFAULT NOW(),
        user_id BIGINT PRIMARY KEY NOT NULL,
        user_name VARCHAR(250) NOT NULL,
        first_name VARCHAR(250),
        last_name VARCHAR(250)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS watches (
        user_id BIGINT,
        watch_name VARCHAR(250),
        price VARCHAR(50),
        characteristics TEXT,
        time TIMESTAMP DEFAULT NOW(),
        FOREIGN KEY (user_id)
            REFERENCES users (user_id)
            ON UPDATE CASCADE
            ON DELETE CASCADE
    )
    """
)

class WatchStates(StatesGroup):
    waiting_for_watch_name = State()
    waiting_for_watch_price = State()

async def create_tables():
    for command in create_db:
        await command_execute(command)

inline_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="buy", callback_data="buy")],
        [InlineKeyboardButton(text="ex", url="ex")]
    ]
)


async def keyboard_handler(message: types.Message):
    await message.answer("Select an option:", reply_markup=inline_kb)



async def connect_db():

    return await asyncpg.connect(user=user, password=password, database=database, host=host, port=port)


async def command_execute(command, arguments = None):

    conn = None
    try:
        conn = await connect_db()
        if arguments is not None:
            await conn.execute(command, *arguments)
        else :
            await conn.execute(command)

    except asyncpg.PostgresError as e:
        raise e
    
    finally:
        if conn is not None:  
            await conn.close()

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




async def user_data_handler(message: types.Message) -> None:
    conn = None
    try:
        conn = await connect_db()
        user = message.from_user
        user_id = user.id
        first_name = user.first_name
        last_name = user.last_name
        user_name = user.username

        record = await conn.fetchval('SELECT user_id FROM users WHERE user_id = $1', user_id)

        if record is None:
            insert_query = """
            INSERT INTO users(time, user_id, user_name, first_name, last_name) 
            VALUES (NOW(), $1, $2, $3, $4);
            """
            await conn.execute(insert_query, user_id, user_name, first_name, last_name)

        await message.answer(f"Hello {first_name}. Do you want to choose a watch??")
    except asyncpg.PostgresError as e:
        print(f"Database error: {str(e)}")
    finally:
        if conn is not None:
            await conn.close()


async def watch_name_handler(message: types.Message, state: FSMContext):
    await state.update_data(watch_name=message.text)
    await message.answer("Enter the price of the watch:")
    await state.set_state(WatchStates.waiting_for_watch_price)

async def watch_price_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    watch_name = data.get("watch_name")
    watch_price = message.text
    await message.answer(f"You chose : {watch_name} for {watch_price}")
    await state.clear()



async def main():
    start = time.perf_counter()
    await create_tables()

    bot = Bot(token=token)
    dp = Dispatcher()

    #print(f"quantity: {len(watches)}")


    dp.message.register(start_handler,user_data_handler, Command("start"))
    dp.message.register(keyboard_handler)
    await get_watches(url)
    dp.message.register(watch_name_handler, WatchStates.waiting_for_watch_name)
    dp.message.register(watch_price_handler, WatchStates.waiting_for_watch_price)
 

    end = time.perf_counter()
    print(f"execution time: {end - start:.6f} seconds")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())