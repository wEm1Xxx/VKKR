"""Модель ролей пользователей (админ, капитан, игрок, зритель)."""

from Models.Base import *


class Roles(Base):
    """Таблица roles: справочник ролей для связи с users.role_id."""

    id = PrimaryKeyField()
    name = CharField(unique=True, max_length=50)

    class Meta:
        table_name = "roles"
