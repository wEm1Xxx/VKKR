"""Общий базовый класс моделей ORM: привязка к одной БД."""

from peewee import *
from Connection.Connection import *


class Base(Model):
    """Родитель всех таблиц; Meta.database задаётся через connect()."""

    class Meta:
        database = connect()
