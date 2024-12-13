import asyncio
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
from DB.FSPevent import FSPevent
from DB.user import User
from DB.models.enums.regions import Regions
from DB.models.enums.FSPevent_status import FSPEventStatus

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)

# Базовая дата для тестов
base_date = datetime.now()
base_date.replace(hour=0, minute=0, second=0, microsecond=0)

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
        place="Технопарк Сколково",
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
        place="Балтийский федеральный университет",
        date_start=base_date + timedelta(days=75),
        date_end=base_date + timedelta(days=76),
        status=FSPEventStatus.APPROVED,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="ML Challenge 2024",
        description="Соревнования по разработке моделей машинного обучения для решения практических задач",
        participants="Специалисты по ML и DS",
        participants_num="150 участников",
        discipline="Машинное обучение",
        region=Regions.TATARSTAN,
        place="Иннополис",
        date_start=base_date + timedelta(days=90),
        date_end=base_date + timedelta(days=92),
        status=FSPEventStatus.CONSIDERATION,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="GameDev Марафон",
        description="Трехдневный марафон по разработке компьютерных игр",
        participants="Разработчики игр всех возрастов",
        participants_num="45 команд",
        discipline="Разработка игр",
        region=Regions.SVERDLOVSK_REGION,
        place="Ельцин Центр",
        date_start=base_date + timedelta(days=105),
        date_end=base_date + timedelta(days=108),
        status=FSPEventStatus.APPROVED,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="Backend Battle",
        description="Соревнования по разработке высоконагруженных серверных приложений",
        participants="Senior разработчики",
        participants_num="100 участников",
        discipline="Backend разработка",
        region=Regions.NIZHNY_NOVGOROD_REGION,
        place="IT-Hub Нижний Новгород",
        date_start=base_date + timedelta(days=120),
        date_end=base_date + timedelta(days=121),
        status=FSPEventStatus.APPROVED,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="Mobile Dev Cup",
        description="Кубок по разработке мобильных приложений",
        participants="iOS и Android разработчики",
        participants_num="80 участников",
        discipline="Мобильная разработка",
        region=Regions.KRASNODAR_TERRITORY,
        place="IT Park Краснодар",
        date_start=base_date + timedelta(days=135),
        date_end=base_date + timedelta(days=137),
        status=FSPEventStatus.CONSIDERATION,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="DevOps Challenge",
        description="Соревнования по автоматизации развертывания и управления инфраструктурой",
        participants="DevOps инженеры",
        participants_num="60 участников",
        discipline="DevOps практики",
        region=Regions.TOMSK_REGION,
        place="Томский политехнический университет",
        date_start=base_date + timedelta(days=150),
        date_end=base_date + timedelta(days=151),
        status=FSPEventStatus.APPROVED,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="Frontend Masters Competition",
        description="Соревнования по разработке современных веб-интерфейсов",
        participants="Frontend разработчики",
        participants_num="120 участников",
        discipline="Frontend разработка",
        region=Regions.ROSTOV_REGION,
        place="Южный IT-парк",
        date_start=base_date + timedelta(days=165),
        date_end=base_date + timedelta(days=166),
        status=FSPEventStatus.APPROVED,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="Blockchain Dev Summit",
        description="Соревнования по разработке смарт-контрактов и блокчейн-приложений",
        participants="Blockchain разработчики",
        participants_num="40 команд",
        discipline="Blockchain разработка",
        region=Regions.BASHKORTOSTAN,
        place="Казанский IT-парк",
        date_start=base_date + timedelta(days=180),
        date_end=base_date + timedelta(days=182),
        status=FSPEventStatus.CONSIDERATION,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="Data Engineering Challenge",
        description="Соревнования по построению масштабируемых систем обработки данных",
        participants="Data Engineers",
        participants_num="90 участников",
        discipline="Data Engineering",
        region=Regions.NOVOSIBIRSK_REGION,
        place="Новосибирский Академпарк",
        date_start=base_date + timedelta(days=195),
        date_end=base_date + timedelta(days=197),
        status=FSPEventStatus.APPROVED,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="Cloud Computing Contest",
        description="Соревнования по разработке облачных решений",
        participants="Cloud архитекторы и разработчики",
        participants_num="70 участников",
        discipline="Облачные технологии",
        region=Regions.SAMARA_REGION,
        place="Самарский IT-центр",
        date_start=base_date + timedelta(days=210),
        date_end=base_date + timedelta(days=211),
        status=FSPEventStatus.CONSIDERATION,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="QA Automation Battle",
        description="Соревнования по автоматизации тестирования",
        participants="QA инженеры",
        participants_num="80 участников",
        discipline="Автоматизация тестирования",
        region=Regions.VOLGOGRAD_REGION,
        place="Волгоградский технопарк",
        date_start=base_date + timedelta(days=225),
        date_end=base_date + timedelta(days=226),
        status=FSPEventStatus.APPROVED,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="Low-Code Platform Challenge",
        description="Соревнования по разработке бизнес-приложений на low-code платформах",
        participants="Low-code разработчики",
        participants_num="50 участников",
        discipline="Low-code разработка",
        region=Regions.YAROSLAVL_REGION,
        place="Ярославский технопарк",
        date_start=base_date + timedelta(days=240),
        date_end=base_date + timedelta(days=241),
        status=FSPEventStatus.CONSIDERATION,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="Embedded Systems Programming",
        description="Соревнования по программированию встраиваемых систем",
        participants="Разработчики встраиваемых систем",
        participants_num="40 команд",
        discipline="Программирование микроконтроллеров",
        region=Regions.CHELYABINSK_REGION,
        place="ЮУрГУ",
        date_start=base_date + timedelta(days=255),
        date_end=base_date + timedelta(days=257),
        status=FSPEventStatus.APPROVED,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="Unity Game Challenge",
        description="Соревнования по разработке игр на Unity",
        participants="Unity разработчики",
        participants_num="30 команд",
        discipline="Unity разработка",
        region=Regions.PERM_TERRITORY,
        place="Технопарк Пермь",
        date_start=base_date + timedelta(days=270),
        date_end=base_date + timedelta(days=272),
        status=FSPEventStatus.APPROVED,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="Quantum Computing Hackathon",
        description="Хакатон по квантовым вычислениям и алгоритмам",
        participants="Специалисты по квантовым вычислениям",
        participants_num="20 команд",
        discipline="Квантовые вычисления",
        region=Regions.MOSCOW_REGION,
        place="Физтех",
        date_start=base_date + timedelta(days=285),
        date_end=base_date + timedelta(days=287),
        status=FSPEventStatus.CONSIDERATION,
        files=[]
    ),
    FSPevent(
        sport="Спортивное программирование",
        title="Cross-Platform Development Cup",
        description="Кубок по кроссплатформенной разработке",
        participants="Cross-platform разработчики",
        participants_num="100 участников",
        discipline="Кроссплатформенная разработка",
        region=Regions.KRASNODAR_TERRITORY,
        place="КубГТУ",
        date_start=base_date + timedelta(days=300),
        date_end=base_date + timedelta(days=301),
        status=FSPEventStatus.APPROVED,
        files=[]
    )
]


async def main():
    # Добавляем новые записи
    await asyncio.sleep(20)
    FSPevent().drop_table()
    for i, event in enumerate(test_events, 1):
        try:
            user = User()
            if user.get_by_region(event.region) is not None:
                event.representative = user.id

            if event.get_by_self() is not None:
                logger.info(f"(Test_fsp_events) Событие {event.title} уже добавлено")
                continue

            event.add()
            logger.info(f"(Test_fsp_events) Добавлено событие {i}: {event.title}")

        except Exception as e:
            logger.error(f"(Test_fsp_events) Ошибка при добавлении события {event.title}: {str(e)}")

    logger.info("(Test_fsp_events) Все тестовые события успешно добавлены в базу данных")
