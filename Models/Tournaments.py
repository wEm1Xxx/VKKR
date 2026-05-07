from Models.Base import *
from Models.Users import Users


class Tournaments(Base):
    id = PrimaryKeyField()
    title = CharField(max_length=255)
    game = CharField(max_length=255)
    format = CharField(max_length=32)
    max_teams = IntegerField()
    start_date = DateTimeField()
    status = CharField(max_length=20, default="draft")
    created_by = ForeignKeyField(
        Users,
        backref="created_tournaments",
        column_name="created_by",
        on_delete="RESTRICT"
    )
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "tournaments"