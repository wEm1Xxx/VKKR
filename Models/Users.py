"""Модель пользователя: учётные данные и роль."""

from Models.Base import *
from Models.Roles import Roles


class Users(Base):
    """Таблица users; используется Flask-Login (get_id, is_authenticated и т.д.)."""

    id = PrimaryKeyField()
    username = CharField(unique=True, max_length=100)
    email = CharField(unique=True, max_length=255)
    password_hash = CharField(max_length=255)
    role_id = ForeignKeyField(
        Roles,
        backref="users",
        column_name="role_id",
        on_delete="RESTRICT"
    )
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "users"

    @property
    def role_name(self):
        """Человекочитаемое имя роли для шаблонов."""
        return self.role_id.name if self.role_id else "viewer"

    @property
    def is_authenticated(self):
        """Требование Flask-Login: залогиненный пользователь считается аутентифицированным."""
        return True

    @property
    def is_active(self):
        """Требование Flask-Login: аккаунт активен."""
        return True

    @property
    def is_anonymous(self):
        """Требование Flask-Login: не аноним, если объект Users загружен."""
        return False

    def get_id(self):
        """Возвращает строковый id для сессии Flask-Login."""
        return str(self.id)
