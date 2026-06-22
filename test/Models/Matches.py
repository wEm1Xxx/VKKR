"""Модель матча в сетке турнира."""

from Models.Base import *
from Models.Tournaments import Tournaments
from Models.Teams import Teams


class Matches(Base):
    """Таблица matches: раунд, пары команд, победитель, статус (pending/veto/finished/confirmed)."""

    id = PrimaryKeyField()
    tournament_id = ForeignKeyField(
        Tournaments,
        backref="matches",
        column_name="tournament_id",
        on_delete="CASCADE"
    )
    round = IntegerField()
    team1_id = ForeignKeyField(
        Teams,
        backref="matches_as_team1",
        column_name="team1_id",
        null=True,
        on_delete="SET NULL"
    )
    team2_id = ForeignKeyField(
        Teams,
        backref="matches_as_team2",
        column_name="team2_id",
        null=True,
        on_delete="SET NULL"
    )
    scheduled_time = DateTimeField(null=True)
    winner_id = ForeignKeyField(
        Teams,
        backref="won_matches",
        column_name="winner_id",
        null=True,
        on_delete="SET NULL"
    )
    status = CharField(max_length=20, default="pending")

    class Meta:
        table_name = "matches"
