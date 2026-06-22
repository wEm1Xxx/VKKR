"""Регистрации команд на турниры."""

from Models.Tournament_registrations import Tournament_registrations


class Tournament_registrationsController:
    """CRUD для tournament_registrations."""

    @classmethod
    def get(cls):
        """Все регистрации."""
        return Tournament_registrations.select()

    @classmethod
    def show(cls, id):
        """Регистрация по id или None."""
        return Tournament_registrations.get_or_none(Tournament_registrations.id == id)

    @classmethod
    def add(cls, tournament_id, team_id):
        """Связывает команду с турниром."""
        return Tournament_registrations.create(
            tournament_id=tournament_id,
            team_id=team_id
        )

    @classmethod
    def update(cls, id, **filds):
        """Обновляет запись регистрации."""
        for key, value in filds.items():
            Tournament_registrations.update({key: value}).where(
                Tournament_registrations.id == id
            ).execute()

    @classmethod
    def delete(cls, id):
        """Удаляет регистрацию по id."""
        Tournament_registrations.delete().where(Tournament_registrations.id == id).execute()


if __name__ == "__main__":
    pass
