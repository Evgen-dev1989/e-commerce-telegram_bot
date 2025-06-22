import asyncio

import asyncpg
import requests
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from lxml import html
from lxml.html import HtmlElement
from selenium import webdriver
from config import database, host, password, port, token, user

url_omega = 'https://www.omegawatches.com/en-au/suggestions/omega-mens-watches'
url_rolex = 'https://www.chrono24.com.au/rolex/index.htm'
url_Jaeger_LeCoultre = "https://www.jaeger-lecoultre.com/au-en/watches/all-watches"
import time
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import types
import requests




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

async def get_watches_omega(url):
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


def get_watches_rolex(url):
    driver = webdriver.Chrome()
    driver.get(url)
    tree = html.fromstring(driver.page_source)
    items = tree.xpath('//div[contains(@class, "js-carousel-cell")]')
    watches = []
    for item in items:
        brand = item.xpath('.//span[contains(@class, "d-block")]/text()')
        brand = brand[0].strip() if brand else ''
        model = item.xpath('.//strong/text()')
        model = model[0].strip() if model else ''
        price = item.xpath('.//p[contains(text(), "from AU$")]/text()')
        price = price[0].strip() if price else ''
        if brand or model or price:
            watches.append({
                'brand': brand,
                'model': model,
                'price': price
            })
    driver.quit()
    return watches



def get_watches_jlc(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)
    tree = html.fromstring(driver.page_source)
    items = tree.xpath('//div[contains(@class, "product-card") and @data-cy="mixed-grid-item"]')
    watches = []
    for item in items:
        name = item.xpath('.//h5[contains(@class, "product-card__name")]/text()')
        name = name[0].strip() if name else ''
        characteristics = item.xpath('.//div[contains(@class, "product-card__specs")]/text()')
        characteristics = characteristics[0].strip() if characteristics else ''
        price = item.xpath('.//span[@data-price="value"]/text()')
        price = price[0].strip() if price else ''
        if name or characteristics or price:
            watches.append({
                'name': name,
                'characteristics': characteristics,
                'price': price
            })
    driver.quit()
    watches = remove_duplicates(watches)
    return watches



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

name_watches = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Omega", callback_data="name_Omega")],
        [InlineKeyboardButton(text="Rolex", callback_data="name_Rolex")],
        [InlineKeyboardButton(text="Jaeger-LeCoultre", callback_data="name_Jaeger-LeCoultre")],
    ]
)

async def watch_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    name = callback.data.replace("name_", "")
    await state.update_data(watch_name=name)
    await callback.message.answer("Choose price from:", reply_markup=price_from_kb)
    await callback.answer()


price_from_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="1000", callback_data="from_1000"),
         InlineKeyboardButton(text="2000", callback_data="from_2000"),
         InlineKeyboardButton(text="3000", callback_data="from_3000")],
        [InlineKeyboardButton(text="4000", callback_data="from_4000"),
         InlineKeyboardButton(text="5000", callback_data="from_5000")]
    ]
)


price_to_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="2000", callback_data="to_2000"),
         InlineKeyboardButton(text="3000", callback_data="to_3000"),
         InlineKeyboardButton(text="4000", callback_data="to_4000")],
        [InlineKeyboardButton(text="5000", callback_data="to_5000"),
         InlineKeyboardButton(text="10000+", callback_data="to_10000")]
    ]
)

async def price_from_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    price_from = callback.data.replace("from_", "")
    await state.update_data(price_from=price_from)
    await callback.message.answer("Choose price to:", reply_markup=price_to_kb)
    await callback.answer()

async def price_to_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    price_to = callback.data.replace("to_", "")
    data = await state.get_data()
    watch_name = data.get("watch_name")
    price_from = data.get("price_from")
    await callback.message.answer(f"You have selected {watch_name} a range: from {price_from} to {price_to}")

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

    dp.callback_query.register(price_from_callback_handler, lambda c: c.data.startswith("from_"))
    dp.callback_query.register(price_to_callback_handler, lambda c: c.data.startswith("to_"))

    dp.message.register(user_data_handler)
    #await get_watches(url)
    #watche_omega = await get_watches_omega(url_omega)
   # print(len(watche_omega))

    #watches_rolex = get_watches_rolex(url_rolex)
    #print(watches_rolex)

    watches_jlc = get_watches_jlc(url_Jaeger_LeCoultre)
    print(len(watches_jlc))
    end = time.perf_counter()
    print(f"execution time: {end - start:.6f} seconds")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())