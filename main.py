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


async def keyboard_handler(message: types.Message):
    await message.answer("Select an option:", reply_markup=name_watches)



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




# async def start_handler(message: types.Message):
#     await message.answer("Welcome to the Omega Watches Bot! Type /watches to see the latest watches.")
#     #await keyboard_handler(message)

async def start_handler(message: types.Message, state: FSMContext):
    await message.answer("Welcome to the Omega Watches Bot! Choose a watch:")
    await message.answer("Choose watch:", reply_markup=name_watches)
    await state.set_state(WatchStates.waiting_for_watch_name)


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

        #await message.answer(f"Hello {first_name}. Do you want to choose a watch??")
    except asyncpg.PostgresError as e:
        print(f"Database error: {str(e)}")
    finally:
        if conn is not None:
            await conn.close()

# async def watch_name_handler(message: types.Message, state: FSMContext):
#     await state.update_data(watch_name=message.text)
#     await message.answer("Enter the price of the watch:")
#     await state.set_state(WatchStates.waiting_for_watch_price)




name_watches = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Omega", callback_data="name_Omega")],
        [InlineKeyboardButton(text="Rolex", callback_data="name_Rolex")],
        [InlineKeyboardButton(text="Jaeger-LeCoultre", callback_data="name_Jaeger-LeCoultre")],
    ]
)

# async def watch_name_handler(message: types.Message, state: FSMContext):
#     await message.answer("Choose price:", reply_markup=name_watches)

async def watch_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    name = callback.data.replace("name_", "")
    await state.update_data(watch_name=name)
    await callback.message.answer("Choose price:", reply_markup=price_kb)
    await state.set_state(WatchStates.waiting_for_watch_price)
    await callback.answer()

price_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="1000", callback_data="price_1000"),
        InlineKeyboardButton(text="2000", callback_data="price_2000"),
        InlineKeyboardButton(text="3000", callback_data="price_3000")],
        [InlineKeyboardButton(text="4000", callback_data="price_4000"),
        InlineKeyboardButton(text="5000+", callback_data="price_5000")]
    ]
)
async def watch_price_handler(message: types.Message, state: FSMContext):
    await message.answer("Choose price:", reply_markup=price_kb)

async def price_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    price = callback.data.replace("price_", "")
    await state.update_data(watch_price=price)
    data = await state.get_data()
    watch_name = data.get("watch_name")
    await callback.message.answer(f"You choose: {watch_name} за {price}")
    await state.clear()
    await callback.answer()



async def main():
    start = time.perf_counter()

    bot = Bot(token=token)
    dp = Dispatcher()

    #print(f"quantity: {len(watches)}")
    await create_tables()

    dp.message.register(start_handler, Command("start"))
    dp.callback_query.register(watch_callback_handler, lambda c: c.data.startswith("name_"))
    dp.message.register(watch_price_handler, WatchStates.waiting_for_watch_price)
    dp.callback_query.register(price_callback_handler, lambda c: c.data.startswith("price_"))
    dp.message.register(user_data_handler)
    #await get_watches(url)
 

    end = time.perf_counter()
    print(f"execution time: {end - start:.6f} seconds")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())