from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv
from DB.FSPevent import FSPevent
from DB.models.enums.regions import Regions
from DB.models.FSPevent_status import FSPEventStatus
from DB.user import User

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)


def add_test_events():
    # Базовая дата для тестов
    base_date = datetime.now()

    # Тестовые записи
    test_events = [
        FSPevent(
            sport="Спортивное программирование",
            title="Всероссийский хакатон 'Digital Break'",
            description="Командные соревнования по созданию цифровых продуктов в сфере образования",
            participants="Смешанные команды 18-35 лет",
            participants_num="50 команд",
            discipline="Продуктовое программирование (хакатон)",
            region=Regions.MOSCOW,
            representative="",
            place="Онлайн",
            date_start=base_date + timedelta(days=15),
            date_end=base_date + timedelta(days=17),
            status=FSPEventStatus.APPROVED,
            files=[]
        ),
        FSPevent(
            sport="Спортивное программирование",
            title="Открытый Кубок по алгоритмическому программированию",
            description="Индивидуальные соревнования по решению алгоритмических задач",
            participants="Мужчины, женщины 16-45 лет",
            participants_num="200 участников",
            discipline="Программирование алгоритмическое",
            region=Regions.SAINT_PETERSBURG,
            representative="",
            place="Университет ИТМО",
            date_start=base_date + timedelta(days=30),
            date_end=base_date + timedelta(days=30),
            status=FSPEventStatus.APPROVED,
            files=[]
        ),
        FSPevent(
            sport="Спортивное программирование",
            title="CTF-турнир 'Безопасный код'",
            description="Командные соревнования по информационной безопасности",
            participants="Смешанные команды 18-30 лет",
            participants_num="32 команды",
            discipline="Программирование систем информационной безопасности",
            region=Regions.NOVOSIBIRSK_REGION,
            representative="",
            place="Технопарк Академгородка",
            date_start=base_date + timedelta(days=45),
            date_end=base_date + timedelta(days=46),
            status=FSPEventStatus.CONSIDERATION,
            files=[]
        ),
        FSPevent(
            sport="Спортивное программирование",
            title="Чемпионат по программированию роботов",
            description="Соревнования по программированию автономных роботов для выполнения заданий на полигоне",
            participants="Юноши, девушки 14-18 лет",
            participants_num="40 участников",
            discipline="Программирование робототехники",
            region=Regions.KALMYKIA,
            representative="",
            place="IT-парк",
            date_start=base_date + timedelta(days=60),
            date_end=base_date + timedelta(days=61),
            status=FSPEventStatus.APPROVED,
            files=[]
        ),
        FSPevent(
            sport="Спортивное программирование",
            title="Дрон-программинг 2024",
            description="Соревнования по программированию беспилотных летательных аппаратов",
            participants="Мужчины, женщины 18-40 лет",
            participants_num="25 команд",
            discipline="Программирование БАС",
            region=Regions.KALININGRAD_REGION,
            representative="",
            place="Балтийский федеральный университет",
            date_start=base_date + timedelta(days=75),
            date_end=base_date + timedelta(days=76),
            status=FSPEventStatus.APPROVED,
            files=[]
        )
    ]

    # Добавляем новые записи
    for i, event in enumerate(test_events, 1):
        try:
            user = User().get_by_region(event.region)
            event.representative = user.id
            event.add()
            logger.info(f"Добавлено событие {i}: {event.title}")
        except Exception as e:
            logger.error(f"Ошибка при добавлении события {event.title}: {str(e)}")
            return

    logger.info("Все тестовые события успешно добавлены в базу данных")

# if __name__ == "__main__" or os.getenv('TEST', 'false').lower() == 'true':
#     add_test_events()
