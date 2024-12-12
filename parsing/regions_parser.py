import asyncio
import requests
from bs4 import BeautifulSoup
import logging
import os
from dotenv import load_dotenv

from DB.user import User
from emailer.EmailService import EmailService

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


def parse_regions():
    try:
        url = "https://fsp-russia.com/region/regions/"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        regions_data = []

        # Сначала обработаем данные Москвы из отдельного контейнера
        moscow_container = soup.find('div', class_='contacts_info')
        if moscow_container:
            logger.debug("Найден контейнер contacts_info")
            # Берем все блоки contact_td
            moscow_tds = moscow_container.find_all('div', class_='contact_td')
            if len(moscow_tds) >= 2:  # Должно быть как минимум 2 блока: заголовки и данные Москвы
                moscow_td = moscow_tds[1]  # Берем второй блок с данными
                logger.debug("Найден блок contact_td для Москвы")

                try:
                    # Находим данные в соответствующих блоках
                    region = moscow_td.find('div', class_='cont sub').find('p', class_='white_region').text.strip()
                    leader = moscow_td.find('div', class_='cont ruk').find('p', class_='white_region').text.strip()
                    contact = moscow_td.find('div', class_='cont con').find('p', class_='white_region').text.strip()

                    logger.debug(f"Извлеченные данные Москвы: {region}, {leader}, {contact}")

                    moscow_data = {
                        'region': region,
                        'leader': leader,
                        'contact': contact,
                        'federal_district': 'Руководство'
                    }
                    regions_data.append(moscow_data)
                    logger.info(f"Успешно обработаны данные Москвы: {region}, {leader}")
                except Exception as e:
                    logger.error(f"Ошибка при обработке данных Москвы: {str(e)}")
            else:
                logger.warning(f"Неверное количество блоков contact_td: {len(moscow_tds)}")
        else:
            logger.warning("Не найден контейнер contacts_info")

        # Затем обработаем все остальные регионы из аккордеона
        accordion = soup.find('div', class_='accordion')
        if accordion:
            for district in accordion.find_all('div', class_='accordion-item'):
                district_name = district.find('h4').text.strip()
                logger.info(f"Обработка федерального округа: {district_name}")

                content = district.find('div', class_='accordion-content')
                if content:
                    contact_tds = content.find_all('div', class_='contact_td')
                    logger.info(f"Найдено {len(contact_tds)} регионов в {district_name}")

                    for contact_td in contact_tds:
                        try:
                            region_data = parse_contact_td(contact_td)
                            if region_data:
                                region_data['federal_district'] = district_name
                                regions_data.append(region_data)
                        except Exception as e:
                            region_name = contact_td.find('div', class_='cont sub')
                            region_name = region_name.find('p',
                                                           class_='white_region').text.strip() if region_name else "Неизвестный регион"
                            logger.error(f"Ошибка при обработке региона {region_name}: {str(e)}")
                else:
                    logger.warning(f"Не найден контент для округа {district_name}")
        else:
            logger.error("Не найден основной аккордеон с регионами")

        # Сохраняем данные в JSON файл
        return regions_data

    except requests.RequestException as e:
        logger.error(f"Ошибка при получении данных с сайта: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при парсинге: {str(e)}")
        return None


def parse_contact_td(contact_td):
    if not contact_td:
        return None

    try:
        # Находим блок с названием региона
        sub_div = contact_td.find('div', class_='cont sub')
        if not sub_div:
            logger.error("Не найден блок с названием региона")
            return None
        region_p = sub_div.find('p', class_='white_region')
        if not region_p:
            logger.error("Не найден тег p с названием региона")
            return None
        region = region_p.text.strip()

        # Находим блок с руководителем
        ruk_div = contact_td.find('div', class_='cont ruk')
        if not ruk_div:
            logger.warning(f"Не найден блок с руководителем для региона {region}")
            leader = ""
        else:
            leader_p = ruk_div.find('p', class_='white_region')
            leader = leader_p.text.strip() if leader_p else ""

        # Находим блок с контактами
        con_div = contact_td.find('div', class_='cont con')
        if not con_div:
            logger.warning(f"Не найден блок с контактами для региона {region}")
            contact = ""
        else:
            contact_p = con_div.find('p', class_='white_region')
            contact = contact_p.text.strip() if contact_p else ""

        return {
            'region': region,
            'leader': leader,
            'contact': contact,
        }
    except Exception as e:
        logger.error(f"(RegionsParser) Ошибка при парсинге contact_td: {str(e)}")
        return None


async def main():
    all_contacts = 0
    added_counter = []
    email_service = EmailService()

    for contact in parse_regions():
        all_contacts += 1
        user: User = User(email=contact["contact"], name=contact["leader"], region=contact["region"])
        if user.get() is not None:
            logger.info(f"(RegionsParser) Пользователь {user.email} уже существует")
            continue

        password = user.add_fsp_admin()
        if password is not None:
            added_counter.append((user.email, password))

    logger.info(f"(RegionsParser) Добавлено {len(added_counter)} контактов из {all_contacts}")
    # for email, password in added_counter:
    #     response = email_service.send_send_password_email(
    #         email if os.getenv('TEST', 'false').lower() == 'false' else "andreisafarov091@gmail.com",
    #         password)  # TODO: отправлять на email
    #     print(response)
    #     if not response:
    #         logger.error(f"(RegionsParser) Ошибка при отправке письма на {email}")
    #     await asyncio.sleep(1)
    #     if os.getenv('TEST', 'false').lower() == 'true':
    #         break

    logger.info("(RegionsParser) Парсинг и отправка писем завершены")


if __name__ == "__main__":
    asyncio.run(main())
