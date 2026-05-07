from Models.Roles import Roles

class RolesController:
    @classmethod
    def get(cls):
        return Roles.select()

    @classmethod
    def show(cls, id):
        return Roles.get_or_none(Roles.id == id)

    @classmethod
    def add(cls, name):
        return Roles.create(name=name)

    @classmethod
    def update(cls, id, **filds):
        for key, value in filds.items():
            Roles.update({key: value}).where(Roles.id == id).execute()

    @classmethod
    def delete(cls, id):
        Roles.delete().where(Roles.id == id).execute()

if __name__ == "__main__":
    pass