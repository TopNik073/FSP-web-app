from celery_app.celery import celery
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
import asyncio
from parsing.sportevents_parser import main as parsing_main
from DB.event import Event
from DB.FSPevent import FSPevent
from DB.user import User
from bot.notifications import send_event_notification
from emailer.EmailService import EmailService
from typing import List

load_dotenv()
logger = logging.getLogger(__name__)

# notifications = [{
#     "sport": str,
#     "search_query": str,
#     "notification_time": datetime,
#     "notification_sent": bool,
#     "event_category": "event" | "category" | "FSP",
#     "event_id": int | None,
#     "email": bool,
#     "telegram": bool,
# }]


@celery.task
def update_events():
    """Обновление списка спортивных событий"""
    try:
        logger.info("Начало обновления спортивных событий")
        event_ids = asyncio.run(parsing_main())
        logger.info(f"Обновлено {len(event_ids)} событий")
        return f"События успешно обновлены. Добавлено/обновлено {len(event_ids)} событий"
    except Exception as e:
        logger.error(f"Ошибка при обновлении событий: {e}")
        raise


@celery.task
def check_upcoming_events():
    """Проверка приближающихся событий и отправка уведомлений"""
    try:
        event_manager = Event()
        users = User(auto_add=False).get_users_with_notifications()
        notifications_sent = 0

        for user in users:
            notifications_updated = False
            notifications_to_remove = []

            for notification in user.notifications:
                if notification.get('notification_sent', False):
                    notification_time = datetime.fromisoformat(notification["notification_time"])
                    if notification_time > datetime.now() + timedelta(days=1):
                        notifications_to_remove.append(notification)
                    continue

                notification_time = datetime.fromisoformat(notification['notification_time'])
                now = datetime.now()
                next_check = now + timedelta(minutes=10)

                # Проверяем, находится ли время уведомления в текущем интервале проверки
                if not (now <= notification_time <= next_check):
                    continue

                events = []
                if notification['event_category'] == 'event' and notification.get('event_id'):
                    event = event_manager.get_by_event_id(notification['event_id'])
                    if event:
                        events = [event]
                        if event_manager.is_event_finished(event):
                            notifications_to_remove.append(notification)
                            continue

                elif notification['event_category'] == 'FSP':
                    events = FSPevent(id=notification['event_id']).get_by_filters()
                else:
                    events = event_manager.get_events_by_filters({
                        'sport': notification['sport'],
                        'search_query': notification['search_query']
                    })

                if events:
                    for event in events:
                        send_notification.delay(
                            message=f"Скоро начнется событие: {event.title} в {event.date_start.strftime('%d.%m.%Y %H:%M')}",
                            event_data={
                                'id': event.event_id,
                                'title': event.title,
                                'sport': event.sport,
                                'start_time': event.date_start.strftime('%d.%m.%Y %H:%M'),
                                'date_start': event.date_start.strftime('%d.%m.%Y %H:%M'),
                                'place': event.place,
                                'notification_time': notification['notification_time']
                            },
                            notification_settings={
                                'telegram': notification['telegram'],
                                'email': notification['email']
                            },
                            user_data={
                                'tg_id': user.tg_id,
                                'email': user.email
                            }
                        )
                        notifications_sent += 1

                    notification['notification_sent'] = True
                    notifications_updated = True

            # Удаляем помеченные уведомления
            for notification in notifications_to_remove:
                user.notifications.remove(notification)
                notifications_updated = True

            # Сохраняем изменения только если были обновления
            if notifications_updated:
                # Создаем новый объект User для сохранения
                updated_user = User(id=user.id)
                if updated_user.get():
                    updated_user.notifications = user.notifications
                    updated_user.update()

        logger.info(f"Отправлено {notifications_sent} уведомлений о предстоящих событиях")
        return f"Отправлено {notifications_sent} уведомлений о предстоящих событиях"
    except Exception as e:
        logger.error(f"Ошибка при проверке приближающихся событий: {e}")
        raise


@celery.task(
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def send_notification(
        self,
        message: str,
        event_data: dict,
        notification_settings: dict,
        user_data: dict
):
    """
    Отправка уведомления пользователю через выбранные каналы связи.
    В случае неудачи будет предпринято до 3 попыток с интервалом в 5 минут.
    
    Args:
        message (str): Текст уведомления
        event_data (dict): Данные о событии
        notification_settings (dict): Настройки уведомлений {'telegram': bool, 'email': bool}
        user_data (dict): Данные пользователя {'tg_id': int, 'email': str}
    """
    try:
        telegram_success = notification_settings["telegram"]
        email_success = notification_settings["email"]

        if notification_settings.get('telegram') and user_data.get('tg_id'):
            telegram_success = send_telegram_notification(
                telegram_id=user_data['tg_id'],
                message=message,
                event_data=event_data
            )

        if notification_settings.get('email') and user_data.get('email'):
            email_success = asyncio.run(send_email_notification(
                email=user_data['email'],
                message=message,
                event_data=event_data
            ))

        if notification_settings["telegram"] != telegram_success and notification_settings["email"] != email_success:
            raise Exception("Не удалось отправить уведомления ни по одному каналу")

        return "Уведомления успешно отправлены"
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {e}")
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error("Превышено максимальное количество попыток отправки уведомления")
            raise


def send_telegram_notification(telegram_id: int, message: str, event_data: dict) -> bool:
    """
    Отправка уведомления в Telegram.
    
    Returns:
        bool: True если уведомление успешно отправлено
    """
    try:
        success = asyncio.run(send_event_notification(
            telegram_id=telegram_id,
            message=message,
            event_data=event_data
        ))

        if not success:
            logger.error(f"Не удалось отправить уведомление в Telegram пользователю {telegram_id}")
            return False

        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления в Telegram: {e}")
        return False


async def send_email_notification(email: str, message: str, event_data: dict) -> bool:
    """
    Отправка уведомления на email.
    
    Returns:
        bool: True если уведомление успешно отправлено
    """
    try:
        emailer = EmailService()
        return emailer.send_event_notification(email, "Событие", event_data)
    except Exception as e:
        logger.error(f"Ошибка при отправке email: {e}")
        return False
