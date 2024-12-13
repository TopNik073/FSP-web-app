import os

from bot.bot import dp, bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import WebAppInfo, Message, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()


@dp.message(Command("start"))
async def callback_start(message: Message, state: FSMContext):
    url = f"https://{os.environ.get('MAIN_URL')}"
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Open Web App", url=url)]]
    )
    await message.answer(f"Здравствуйте! Этот канал предназначен для уведомлений о спортивных событиях. Вы можете подписаться на события, которые вас интересуют, и получать уведомления о них.\nГлавный сайт👇", reply_markup=markup)
