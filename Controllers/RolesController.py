"""CRUD для справочника ролей."""

from Models.Roles import Roles


class RolesController:
    """Операции над таблицей roles."""

    @classmethod
    def get(cls):
        """Все роли."""
        return Roles.select()

    @classmethod
    def show(cls, id):
        """Роль по id или None."""
        return Roles.get_or_none(Roles.id == id)

    @classmethod
    def add(cls, name):
        """Создаёт роль с именем name."""
        return Roles.create(name=name)

    @classmethod
    def update(cls, id, **filds):
        """Обновляет поля роли."""
        for key, value in filds.items():
            Roles.update({key: value}).where(Roles.id == id).execute()

    @classmethod
    def delete(cls, id):
        """Удаляет роль по id."""
        Roles.delete().where(Roles.id == id).execute()


if __name__ == "__main__":
    pass
