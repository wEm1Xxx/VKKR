from Models.Tournaments import Tournaments
from Models.Tournament_registrations import Tournament_registrations
from Models.Matches import Matches


class TournamentsController:
    @classmethod
    def get(cls):
        return Tournaments.select()

    @classmethod
    def show(cls, id):
        return Tournaments.get_or_none(Tournaments.id == id)

    @classmethod
    def add(cls, title, game, format, max_teams, start_date, created_by, status="registration"):
        return Tournaments.create(
            title=title,
            game=game,
            format=format,
            max_teams=max_teams,
            start_date=start_date,
            status=status,
            created_by=created_by
        )

    @classmethod
    def update(cls, id, **filds):
        for key, value in filds.items():
            Tournaments.update({key: value}).where(Tournaments.id == id).execute()

    @classmethod
    def delete(cls, id):
        Tournament_registrations.delete().where(Tournament_registrations.tournament_id == id).execute()
        Matches.delete().where(Matches.tournament_id == id).execute()
        Tournaments.delete().where(Tournaments.id == id).execute()


if __name__ == "__main__":
    pass