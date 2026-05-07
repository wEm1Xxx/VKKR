from Models.Tournament_registrations import Tournament_registrations


class Tournament_registrationsController:
    @classmethod
    def get(cls):
        return Tournament_registrations.select()

    @classmethod
    def show(cls, id):
        return Tournament_registrations.get_or_none(Tournament_registrations.id == id)

    @classmethod
    def add(cls, tournament_id, team_id):
        return Tournament_registrations.create(
            tournament_id=tournament_id,
            team_id=team_id
        )

    @classmethod
    def update(cls, id, **filds):
        for key, value in filds.items():
            Tournament_registrations.update({key: value}).where(
                Tournament_registrations.id == id
            ).execute()

    @classmethod
    def delete(cls, id):
        Tournament_registrations.delete().where(Tournament_registrations.id == id).execute()


if __name__ == "__main__":
    pass