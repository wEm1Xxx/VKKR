"""Регистрация команды на турнир."""

from Models.Base import *
from Models.Tournaments import Tournaments
from Models.Teams import Teams


class Tournament_registrations(Base):
    """Таблица tournament_registrations: какая team участвует в каком tournament."""

    id = PrimaryKeyField()
    tournament_id = ForeignKeyField(
        Tournaments,
        backref="registrations",
        column_name="tournament_id",
        on_delete="CASCADE"
    )
    team_id = ForeignKeyField(
        Teams,
        backref="tournament_registrations",
        column_name="team_id",
        on_delete="CASCADE"
    )
    registered_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "tournament_registrations"
        indexes = (
            (("tournament_id", "team_id"), True),
        )
