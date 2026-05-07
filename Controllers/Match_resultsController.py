from Models.Match_results import Match_results


class Match_resultsController:
    @classmethod
    def get(cls):
        return Match_results.select()

    @classmethod
    def show(cls, id):
        return Match_results.get_or_none(Match_results.id == id)

    @classmethod
    def add(cls, match_id, score_team1, score_team2, reported_by, confirmed_by=None, confirmed_at=None):
        return Match_results.create(
            match_id=match_id,
            score_team1=score_team1,
            score_team2=score_team2,
            reported_by=reported_by,
            confirmed_by=confirmed_by,
            confirmed_at=confirmed_at
        )

    @classmethod
    def update(cls, id, **filds):
        for key, value in filds.items():
            Match_results.update({key: value}).where(Match_results.id == id).execute()

    @classmethod
    def delete(cls, id):
        Match_results.delete().where(Match_results.id == id).execute()


if __name__ == "__main__":
    pass