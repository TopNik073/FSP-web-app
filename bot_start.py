import asyncio
import logging
from parsing import archive_parser, sportevents_parser, regions_parser
import test_fsp_events
from bot.bot import dp, bot
from bot import handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def main():
    # logger.info("Начало парсинга спортивных событий")
    # await sportevents_parser.main()

    logger.info("Начало парсинга архива")
    await archive_parser.main()

    logger.info("Начало парсинга результатов")
    await regions_parser.main()

    logger.info("Начало добавления тестовых событий")
    await test_fsp_events.main()

    logger.info("Запуск бота")
    # await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
