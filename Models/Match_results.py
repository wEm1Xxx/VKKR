"""Итоговый счёт матча и подтверждение админом."""

from Models.Base import *
from Models.Matches import Matches
from Models.Users import Users


class Match_results(Base):
    """Таблица match_results: счёт серии, кто отправил, кто подтвердил (админ)."""

    id = PrimaryKeyField()
    match_id = ForeignKeyField(
        Matches,
        backref="results",
        column_name="match_id",
        on_delete="CASCADE"
    )
    score_team1 = IntegerField()
    score_team2 = IntegerField()
    reported_by = ForeignKeyField(
        Users,
        backref="reported_results",
        column_name="reported_by",
        on_delete="RESTRICT"
    )
    confirmed_by = ForeignKeyField(
        Users,
        backref="confirmed_results",
        column_name="confirmed_by",
        null=True,
        on_delete="SET NULL"
    )
    confirmed_at = DateTimeField(null=True)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "match_results"
