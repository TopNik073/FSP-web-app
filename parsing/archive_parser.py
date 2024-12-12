import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

from DB.FSPevent_archive import FSPevent_archive

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArchiveParser:
    def __init__(self):
        self.base_url = "https://fsp-russia.com/calendar/archive/"

    def parse_date(self, date_str):
        try:
            # Преобразование даты из формата "02 - 04 июня 2024 г." в datetime
            date_str = date_str.replace("г.", "").strip()
            parts = date_str.split(" - ")

            months_ru = {
                'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
                'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
                'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
            }

            if len(parts) == 2:
                # Удаляем ведущие нули перед преобразованием в int
                start_day = int(parts[0].strip().lstrip('0'))
                end_parts = parts[1].strip().split()
                end_day = int(end_parts[0].lstrip('0'))
                month = months_ru[end_parts[1]]
                year = int(end_parts[2])

                start_date = datetime(year, month, start_day)
                end_date = datetime(year, month, end_day)
                
                # Добавляем время (начало и конец дня)
                start_date = start_date.replace(hour=0, minute=0, second=0)
                end_date = end_date.replace(hour=0, minute=0, second=0)
                
                return start_date, end_date
                
            return None, None
        except Exception as e:
            logger.error(f"Ошибка при парсинге даты {date_str}: {str(e)}")
            return None, None

    def parse_events(self):
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            events = []
            archive_items = soup.find_all('div', class_='archive_item')

            for item in archive_items:
                try:
                    event = {}

                    # Парсинг ссылки
                    link = item.find('a')
                    if link:
                        event['url'] = f"https://fsp-russia.com{link['href']}"

                    # Парсинг даты
                    date_div = item.find('div', class_='date')
                    if date_div:
                        day = date_div.find('p', class_='bold')
                        month = date_div.find_all('p')[1]
                        if day and month:
                            event['day'] = day.text.strip()
                            event['month'] = month.text.strip()

                    # Парсинг названия
                    title = item.find('div', class_='title')
                    if title:
                        event['title'] = title.text.strip()

                    # Парсинг информации о местоположении и дате проведения
                    location_div = item.find('div', class_='location')
                    if location_div:
                        date_min = location_div.find('div', class_='date_min')
                        if date_min:
                            date_text = date_min.text.strip()
                            start_date, end_date = self.parse_date(date_text)
                            event['start_date'] = start_date
                            event['end_date'] = end_date
                            event['date_range'] = date_text

                        city = location_div.find('div', class_='city')
                        if city:
                            event['city'] = city.text.strip()

                    # Парсинг дисциплины
                    discipline = item.find('div', class_='discipline')
                    if discipline:
                        event['discipline'] = discipline.text.strip()

                    # Парсинг категории участников
                    mens = item.find('div', class_='mens')
                    if mens:
                        event['participants'] = mens.text.strip()

                    events.append(event)

                except Exception as e:
                    logger.error(f"Ошибка при парсинге события: {str(e)}")
                    continue

            return events

        except Exception as e:
            logger.error(f"Ошибка при получении данных с сайта: {str(e)}")
            return []

    def save_to_db(self):
        events = self.parse_events()
        for event in events:
            event_obj = FSPevent_archive(
                title=event['title'],
                place=event['city'],
                participants=event['participants'],
                discipline=event['discipline'],
                date_start=event['start_date'],
                date_end=event['end_date'],
            )

            if event_obj.get_by_self() is not None:
                logger.info(f"(ArchiveParser) Событие {event['title']} уже существует в базе данных")
                continue

            event_obj.add()
            logger.info(f"(ArchiveParser) Событие {event['title']} добавлено в базу данных")


async def main():
    parser = ArchiveParser()
    parser.save_to_db()

if __name__ == "__main__":
    asyncio.run(main())
