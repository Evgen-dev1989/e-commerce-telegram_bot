from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from config import token


bot = Bot(token=token)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_handler(message: Message):
    await message.reply("hello")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)