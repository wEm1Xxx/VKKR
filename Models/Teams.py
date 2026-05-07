from Models.Base import *
from Models.Users import Users


class Teams(Base):
    id = PrimaryKeyField()
    name = CharField(unique=True, max_length=120)
    captain_id = ForeignKeyField(
        Users,
        backref="captain_teams",
        column_name="captain_id",
        on_delete="RESTRICT"
    )
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "teams"