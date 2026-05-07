from Models.Base import *


class Roles(Base):
    id = PrimaryKeyField()
    name = CharField(unique=True, max_length=50)

    class Meta:
        table_name = "roles"