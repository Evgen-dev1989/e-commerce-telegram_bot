import asyncio
import time

import asyncpg
import requests
import undetected_chromedriver as uc
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from lxml import html
from selenium import webdriver
from collections import defaultdict

from config import database, host, password, port, token, user

url_omega = 'https://www.omegawatches.com/en-au/suggestions/omega-mens-watches'
url_rolex = 'https://www.chrono24.com.au/rolex/index.html'
url_Jaeger_LeCoultre = "https://www.jaeger-lecoultre.com/au-en/watches/all-watches"
dp = Dispatcher()
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

def get_watches_omega(url):
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
    options = uc.ChromeOptions()
    options.add_argument('--disable-gpu')
    driver = uc.Chrome(options=options)
    driver.get(url)
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
        consent_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "js-cookie-accept-all")]'))
        )
        consent_btn.click()
        time.sleep(2)
    except Exception as e:
        print("Cookie consent button not found or not clicked:", e)

    for _ in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    tree = html.fromstring(driver.page_source)
 
    cards = tree.xpath('//div[contains(@class, "text-sm text-sm-md text-bold text-ellipsis")]/ancestor::div[contains(@class, "d-flex align-items-center")]/parent::div')
    watches = []
    for card in cards:

        name = card.xpath('.//div[contains(@class, "text-sm text-sm-md text-bold text-ellipsis")]/text()')
        name = name[0].strip() if name else ''

        desc = card.xpath('.//div[contains(@class, "text-sm text-sm-md text-ellipsis m-b-2")]/text()')
        desc = desc[0].strip() if desc else ''

        price = card.xpath('.//span[@class="currency"]/following-sibling::text()')
        price = price[0].strip() if price else ''
        if name or desc or price:
            watches.append({
                'name': name,
                'characteristics': desc,
                'price': price
            })
    try:
        driver.quit()
    except Exception:
        pass
    del driver
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



async def show_choice_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    watch_name = data.get("watch_name")
    price_from = data.get("price_from")
    price_to = data.get("price_to")

    if price_from is None or price_to is None:
        await message.answer("Price range is not set. Please select price range again.")
        return

    if watch_name == "Omega":
        watches = get_watches_omega(url_omega)
    elif watch_name == "Rolex":
        watches = get_watches_rolex(url_rolex)
    else:
        watches = get_watches_jlc(url_Jaeger_LeCoultre)

    filtered = []
    for watch in watches:
        try:
            price_str = watch.get('price', '')
            price_digits = ''.join(c for c in price_str if c.isdigit() or c == '.')
            if not price_digits:
                continue
            price = float(price_digits)
            if float(price_from) <= price <= float(price_to):
                filtered.append(watch)
        except ValueError:
            continue

    if not filtered:
        await message.answer("No watches found for your selection.")
        await state.clear()
        return

    await state.update_data(filtered_watches=filtered, watches_index=0)
    await send_next_batch(message, state)


async def send_next_batch(message: types.Message, state: FSMContext):
    data = await state.get_data()
    watches = data.get("filtered_watches", [])
    index = data.get("watches_index", 0)
    batch = watches[index:index+4]
    if not batch:
        await message.answer("No more watches.")
        await state.clear()
        return

    for i, watch in enumerate(batch):
        msg = (
            f"Name: {watch.get('name', '')}\n"
            f"Characteristics: {watch.get('characteristics', '')}\n"
            f"Price: {watch.get('price', '')}"
        )
     
        track_data = f"track_{index + i}"
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Follow", callback_data=track_data)]
            ]
        )
        await message.answer(msg, reply_markup=kb)

    index += 4
    await state.update_data(watches_index=index)
    if index < len(watches):
        await message.answer("Send /more to see more watches.")
    else:
        await message.answer("No more watches.")
        await state.clear()


@dp.callback_query(lambda c: c.data.startswith("track_"))
async def track_watch_callback(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    watches = data.get("filtered_watches", [])
    idx = int(callback.data.replace("track_", ""))
    if 0 <= idx < len(watches):
        watch = watches[idx]
        conn = None
        try:    
            conn = await connect_db()
            user = callback.from_user
            user_id = user.id

            record = await conn.fetchval(
                'SELECT 1 FROM watches WHERE user_id = $1 AND watch_name = $2',
                user_id, watch_name
            )
            if record:
                await callback.message.answer("You are already tracking this watch.")
                return
            
            watch_name = watch.get('name', '')
            price = watch.get('price', '')
            characteristics = watch.get('characteristics', '')

            insert_query = """
                INSERT INTO watches(user_id, watch_name, price, characteristics) 
                VALUES ($1, $2, $3, $4);
                """
            await conn.execute(insert_query, user_id, watch_name, price, characteristics)

        
        except asyncpg.PostgresError as e:
            print(f"Database error: {str(e)}")
        finally:
            if conn is not None:
                await conn.close()

        await callback.message.answer(
            f"You have added to tracking:\n"
            f"Name: {watch.get('name', '')}\n"
            f"Characteristics: {watch.get('characteristics', '')}\n"
            f"Price: {watch.get('price', '')}"
        )
    await callback.answer("Added to watchlist!")




async def check_track_watches(user_id, bot):
    conn = None
    try:
        conn = await connect_db()
        db_watches = await conn.fetch('SELECT id, watch_name, price, characteristics FROM watches WHERE user_id = $1', user_id)

        brands = defaultdict(list)
        for db_watch in db_watches:
            brands[db_watch['watch_name']].append(db_watch)


        actual_data = {
            "Omega": get_watches_omega(url_omega),
            "Rolex": get_watches_rolex(url_rolex),
            "Jaeger-LeCoultre": get_watches_jlc(url_Jaeger_LeCoultre)
        }

        for brand, watches in brands.items():
            actual_watches = actual_data[brand]
            for db_watch in watches:
                actual = next((w for w in actual_watches if w['name'] == db_watch['watch_name']), None)
                if not actual:
                    continue

                updates = []
                if db_watch['price'] != actual['price']:
                    await conn.execute('UPDATE watches SET price = $1 WHERE id = $2', actual['price'], db_watch['id'])
                    updates.append(f"Price changed: {db_watch['price']} → {actual['price']}")
                if db_watch['characteristics'] != actual['characteristics']:
                    await conn.execute('UPDATE watches SET characteristics = $1 WHERE id = $2', actual['characteristics'], db_watch['id'])
                    updates.append(f"Characteristics changed: {db_watch['characteristics']} → {actual['characteristics']}")

                if updates:
                    msg = f"Watch '{db_watch['watch_name']}' updated:\n" + "\n".join(updates)
                    await bot.send_message(user_id, msg)

    except asyncpg.PostgresError as e:
        print(f"Database error: {str(e)}")
    finally:
        if conn is not None:
            await conn.close()




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
        [InlineKeyboardButton(text="40000", callback_data="from_40000"),
         InlineKeyboardButton(text="50000", callback_data="from_50000")]
    ]
)

price_to_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="2000", callback_data="to_2000"),
         InlineKeyboardButton(text="3000", callback_data="to_3000"),
         InlineKeyboardButton(text="40000", callback_data="to_40000")],
        [InlineKeyboardButton(text="50000", callback_data="to_50000"),
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
    await state.update_data(price_to=price_to)  
    data = await state.get_data()
    watch_name = data.get("watch_name")
    price_from = data.get("price_from")
    await callback.message.answer(
        f"You have selected {watch_name} a range: from {price_from} to {price_to}. Do you want look /watches ?"
    )
    await callback.answer()


async def main():
    start = time.perf_counter()

    bot = Bot(token=token)


    #print(f"quantity: {len(watches)}")
    await create_tables()

    dp.message.register(start_handler, Command("start"))
    dp.callback_query.register(watch_callback_handler, lambda c: c.data.startswith("name_"))

    dp.callback_query.register(price_from_callback_handler, lambda c: c.data.startswith("from_"))
    dp.callback_query.register(price_to_callback_handler, lambda c: c.data.startswith("to_"))
 
    dp.message.register(show_choice_user, Command("watches"))
    dp.message.register(send_next_batch, Command("more"))
    dp.callback_query.register(track_watch_callback, lambda c: c.data.startswith("track_"))
    dp.message.register(user_data_handler)

    conn = await connect_db()
    user_ids = await conn.fetch('SELECT user_id FROM users')
    await conn.close()

    for record in user_ids:
        await check_track_watches(record['user_id'], bot)


    end = time.perf_counter()
    print(f"execution time: {end - start:.6f} seconds")
    #print(get_watches_rolex(url_rolex))
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())