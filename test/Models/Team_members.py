"""Связь пользователь ↔ команда (состав)."""

from Models.Base import *
from Models.Teams import Teams
from Models.Users import Users


class Team_members(Base):
    """Таблица team_members: кто из users входит в какую team (уникальная пара team+user)."""

    id = PrimaryKeyField()
    team_id = ForeignKeyField(
        Teams,
        backref="memberships",
        column_name="team_id",
        on_delete="CASCADE"
    )
    user_id = ForeignKeyField(
        Users,
        backref="team_memberships",
        column_name="user_id",
        on_delete="CASCADE"
    )
    joined_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "team_members"
        indexes = (
            (("team_id", "user_id"), True),
        )
