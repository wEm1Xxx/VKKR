"""Один шаг пик/бана карт CS2 для матча."""

from Models.Base import *
from Models.Matches import Matches
from Models.Teams import Teams


class Cs2_pickban(Base):
    """Таблица cs2_pickban: шаг (1–7), действие ban/pick/decider, карта, чья команда ходила."""

    id = PrimaryKeyField()
    match_id = ForeignKeyField(Matches, backref="cs2_pickbans", on_delete="CASCADE")
    step = IntegerField()
    action = CharField(max_length=20)
    map_name = CharField(max_length=64)
    team_id = ForeignKeyField(Teams, null=True, on_delete="SET NULL")

    class Meta:
        table_name = "cs2_pickban"


if __name__ == "__main__":
    pass
