"""Команды: создание вместе с записью капитана в состав."""

from Models.Teams import Teams
from Models.Team_members import Team_members


class TeamsController:
    """Операции над teams и связанными team_members."""

    @classmethod
    def get(cls):
        """Все команды."""
        return Teams.select()

    @classmethod
    def show(cls, id):
        """Команда по id или None."""
        return Teams.get_or_none(Teams.id == id)

    @classmethod
    def add(cls, name, captain_id):
        """Создаёт команду и сразу добавляет капитана в team_members."""
        team = Teams.create(name=name, captain_id=captain_id)
        Team_members.create(team_id=team.id, user_id=captain_id)
        return team

    @classmethod
    def update(cls, id, **filds):
        """Обновляет поля команды."""
        for key, value in filds.items():
            Teams.update({key: value}).where(Teams.id == id).execute()

    @classmethod
    def delete(cls, id):
        """Удаляет всех участников команды и саму команду."""
        Team_members.delete().where(Team_members.team_id == id).execute()
        Teams.delete().where(Teams.id == id).execute()


if __name__ == "__main__":
    pass
