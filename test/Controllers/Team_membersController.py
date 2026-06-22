"""Состав команд: связь user ↔ team."""

from Models.Team_members import Team_members


class Team_membersController:
    """CRUD для team_members."""

    @classmethod
    def get(cls):
        """Все записи состава."""
        return Team_members.select()

    @classmethod
    def show(cls, id):
        """Запись по id или None."""
        return Team_members.get_or_none(Team_members.id == id)

    @classmethod
    def add(cls, team_id, user_id):
        """Добавляет игрока в команду."""
        return Team_members.create(team_id=team_id, user_id=user_id)

    @classmethod
    def update(cls, id, **filds):
        """Обновляет запись состава."""
        for key, value in filds.items():
            Team_members.update({key: value}).where(Team_members.id == id).execute()

    @classmethod
    def delete(cls, id):
        """Удаляет запись состава по id."""
        Team_members.delete().where(Team_members.id == id).execute()


if __name__ == "__main__":
    pass
