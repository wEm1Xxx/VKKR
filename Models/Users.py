from Models.Base import *
from Models.Roles import Roles


class Users(Base):
    id = PrimaryKeyField()
    username = CharField(unique=True, max_length=100)
    email = CharField(unique=True, max_length=255)
    password_hash = CharField(max_length=255)
    role_id = ForeignKeyField(
        Roles,
        backref="users",
        column_name="role_id",
        on_delete="RESTRICT"
    )
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = "users"

    @property
    def role_name(self):
        return self.role_id.name if self.role_id else "viewer"

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)