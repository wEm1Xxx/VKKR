"""Альтернативный контроллер авторизации (создание user по имени роли)."""

import bcrypt
from Models.Users import Users
from Models.Roles import Roles


class AuthController:
    """Регистрация и вход без role_id — через текстовое имя роли."""

    @classmethod
    def get(cls):
        """Все пользователи."""
        return Users.select()

    @classmethod
    def show(cls, id):
        """Пользователь по id или None."""
        return Users.get_or_none(Users.id == id)

    @classmethod
    def add(cls, username, email, password, role_name="viewer"):
        """Создаёт user с ролью по имени role_name."""
        role = Roles.get_or_none(Roles.name == role_name)
        if role is None:
            return None

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(rounds=12)
        ).decode("utf-8")

        return Users.create(
            username=username,
            email=email,
            password_hash=password_hash,
            role_id=role.id
        )

    @classmethod
    def update(cls, id, **filds):
        """Произвольное обновление полей users."""
        for key, value in filds.items():
            Users.update({key: value}).where(Users.id == id).execute()

    @classmethod
    def delete(cls, id):
        """Удаление пользователя."""
        Users.delete().where(Users.id == id).execute()

    @classmethod
    def login(cls, login_value, password):
        """Проверка входа: возвращает объект Users или None."""
        user = Users.get_or_none(Users.email == login_value)
        if user is None:
            user = Users.get_or_none(Users.username == login_value)

        if user is None:
            return None

        if bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            return user
        return None


if __name__ == "__main__":
    pass
