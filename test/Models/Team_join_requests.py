"""Заявка игрока на вступление в команду."""

from Models.Base import *
from Models.Teams import Teams
from Models.Users import Users


class Team_join_requests(Base):
    """Таблица team_join_requests: pending / approved / rejected между player и team."""

    id = PrimaryKeyField()
    team_id = ForeignKeyField(
        Teams,
        backref="join_requests",
        column_name="team_id",
        on_delete="CASCADE"
    )
    player_id = ForeignKeyField(
        Users,
        backref="sent_join_requests",
        column_name="player_id",
        on_delete="CASCADE"
    )
    status = CharField(max_length=20, default="pending")  # pending/approved/rejected
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "team_join_requests"
        indexes = (
            (("team_id", "player_id"), True),
        )
