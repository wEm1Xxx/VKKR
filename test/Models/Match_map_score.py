"""Счёт по отдельной карте в серии CS2 (раунды)."""

from Models.Base import *
from Models.Matches import Matches


class Match_map_score(Base):
    """Таблица match_map_score: детализация BO3 по картам для одного match."""

    id = PrimaryKeyField()
    match_id = ForeignKeyField(Matches, backref="map_scores", on_delete="CASCADE")
    map_name = CharField(max_length=64)
    team1_rounds = IntegerField()
    team2_rounds = IntegerField()
    map_order = IntegerField()

    class Meta:
        table_name = "match_map_score"


if __name__ == "__main__":
    pass
