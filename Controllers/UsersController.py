import bcrypt
from Models.Users import Users
from Models.Roles import Roles


class UsersController:
    @classmethod
    def get(cls):
        return Users.select()

    @classmethod
    def show(cls, id):
        return Users.get_or_none(Users.id == id)

    @classmethod
    def show_login(cls, login):
        user = Users.get_or_none(Users.email == login)
        if user is None:
            user = Users.get_or_none(Users.username == login)
        return user

    @classmethod
    def add(cls, username, email, password, role_id=None, role_name="viewer"):
        if role_id is None:
            role = Roles.get_or_none(Roles.name == role_name)
            if role is None:
                return None
            role_id = role.id

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(rounds=12)
        ).decode("utf-8")

        return Users.create(
            username=username,
            email=email,
            password_hash=password_hash,
            role_id=role_id
        )

    @classmethod
    def registration(cls, login, password, role_id=None):
        # login может быть username или email
        is_email = "@" in login
        username = login if not is_email else login.split("@")[0]
        email = login if is_email else f"{login}@local.dev"

        if Users.get_or_none(Users.username == username):
            return False
        if Users.get_or_none(Users.email == email):
            return False

        if role_id is None:
            role = Roles.get_or_none(Roles.name == "viewer")
            if role is None:
                return False
            role_id = role.id

        created = cls.add(
            username=username,
            email=email,
            password=password,
            role_id=role_id
        )
        return created is not None

    @classmethod
    def auth(cls, login, password):
        user = cls.show_login(login)
        if user is None:
            return False

        return bcrypt.checkpw(
            password.encode("utf-8"),
            user.password_hash.encode("utf-8")
        )

    @classmethod
    def update(cls, id, **filds):
        if "password" in filds:
            raw_password = filds.pop("password")
            filds["password_hash"] = bcrypt.hashpw(
                raw_password.encode("utf-8"),
                bcrypt.gensalt(rounds=12)
            ).decode("utf-8")

        for key, value in filds.items():
            Users.update({key: value}).where(Users.id == id).execute()

    @classmethod
    def delete(cls, id):
        Users.delete().where(Users.id == id).execute()


if __name__ == "__main__":
    UsersController.add('player','player@player.player','player','3')