from enum import Enum


class UserRoles(Enum):
    REGIONAL_ADMIN = "Региональный представитель"
    CENTRAL_ADMIN = "Центральный представитель"
    USER = "Пользователь"
    ADMIN = "Администратор"
