"""
Подключение к MySQL через Peewee.

Параметры читаются из .env в корне проекта (см. .env.example).
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from peewee import MySQLDatabase

# Загружаем переменные до первого connect() (вызывается из Models.Base)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def connect():
    """Создаёт объект MySQLDatabase с настройками из переменных окружения (или значения по умолчанию)."""
    return MySQLDatabase(
        os.getenv("MYSQL_DATABASE", "tournament"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
    )


if __name__ == "__main__":
    print(connect().connect())
