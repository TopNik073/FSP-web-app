from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.bot import bot
import logging
import os
from dotenv import load_dotenv
from aiogram.exceptions import TelegramBadRequest
load_dotenv()

logger = logging.getLogger(__name__)


async def send_event_notification(
    telegram_id: int,
    message: str,
    event_data: dict
) -> bool:
    """
    Отправляет уведомление о событии через Telegram.
    
    Args:
        telegram_id (int): ID пользователя в Telegram
        message (str): Текст сообщения
        event_data (dict): Данные о событии
    
    Returns:
        bool: True если уведомление успешно отправлено
    """
    try:
        # Создаем клавиатуру с кнопкой для перехода к событию
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="Подробнее о событии",
                url=f"https://{os.getenv('MAIN_URL')}/events/{event_data['id']}"
            )
        ]])

        # Форматируем сообщение с дополнительной информацией
        detailed_message = (
            f"{message}\n\n"
            f"🏆 Вид спорта: {event_data['sport']}\n"
            f"📍 Место проведения: {event_data['place']}\n"
            f"🕒 Начало: {event_data['start_time']}"
        )

        # Отправляем сообщение с клавиатурой
        await bot.send_message(
            chat_id=telegram_id,
            text=detailed_message,
            reply_markup=keyboard
        )
        return True
    
    except TelegramBadRequest as e:
        logger.info(f"Пользователь {telegram_id} отписался от уведомлений", e)
        return True

    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления в Telegram для пользователя {telegram_id}: {e}")
        return False 
