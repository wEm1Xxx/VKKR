"""Матчи турнира и связанные результаты."""

from Models.Matches import Matches
from Models.Match_results import Match_results


class MatchesController:
    """Операции над matches; при удалении матча чистятся match_results."""

    @classmethod
    def get(cls):
        """Все матчи."""
        return Matches.select()

    @classmethod
    def show(cls, id):
        """Матч по id или None."""
        return Matches.get_or_none(Matches.id == id)

    @classmethod
    def add(cls, tournament_id, round, team1_id=None, team2_id=None, scheduled_time=None, winner_id=None, status="pending"):
        """Создаёт матч в сетке турнира."""
        return Matches.create(
            tournament_id=tournament_id,
            round=round,
            team1_id=team1_id,
            team2_id=team2_id,
            scheduled_time=scheduled_time,
            winner_id=winner_id,
            status=status
        )

    @classmethod
    def update(cls, id, **filds):
        """Обновляет поля матча."""
        for key, value in filds.items():
            Matches.update({key: value}).where(Matches.id == id).execute()

    @classmethod
    def delete(cls, id):
        """Удаляет результаты матча и сам матч."""
        Match_results.delete().where(Match_results.match_id == id).execute()
        Matches.delete().where(Matches.id == id).execute()


if __name__ == "__main__":
    pass
