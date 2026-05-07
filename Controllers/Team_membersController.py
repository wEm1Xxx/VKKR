from Models.Team_members import Team_members


class Team_membersController:
    @classmethod
    def get(cls):
        return Team_members.select()

    @classmethod
    def show(cls, id):
        return Team_members.get_or_none(Team_members.id == id)

    @classmethod
    def add(cls, team_id, user_id):
        return Team_members.create(team_id=team_id, user_id=user_id)

    @classmethod
    def update(cls, id, **filds):
        for key, value in filds.items():
            Team_members.update({key: value}).where(Team_members.id == id).execute()

    @classmethod
    def delete(cls, id):
        Team_members.delete().where(Team_members.id == id).execute()


if __name__ == "__main__":
    pass