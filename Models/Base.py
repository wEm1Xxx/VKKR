from peewee import *
from Connection.Connection import *

class Base(Model):
    class Meta:
        database = connect()