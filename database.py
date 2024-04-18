from peewee import *
from playhouse.postgres_ext import *
import os
import psycopg2

database = PostgresqlExtDatabase(database=os.environ.get("DB_NAME"), host=os.environ.get("DB_HOST"), port=os.environ.get("DB_PORT"), user=os.environ.get("DB_USER"), password=os.environ.get("DB_PASSWORD"))


class BaseModel(Model):
    class Meta:
        database = database


class ProductDb(BaseModel):
    product_id = IntegerField(unique=True)
    product_name = CharField(null=True)
    product_type = CharField(null=True)
    product_in_stock = BooleanField(null=True)
    product_desc = CharField(null=True)
    product_price = FloatField(null=True)
    product_height = FloatField(null=True)
    product_weight = FloatField(null=True)
    product_image = CharField(null=True)


class CommandDb(BaseModel):
    command_id = AutoField(unique=True)
    command = BinaryJSONField(null=False)
    command_email = CharField(null=True)
    command_country = CharField(null=True)
    command_address = CharField(null=True)
    command_postal_code = CharField(null=True)
    command_city = CharField(null=True)
    command_province = CharField(null=True)
    command_paid = BooleanField(default=False)
    command_amount_charged = IntegerField(null=True)
    command_transaction_id = CharField(null=True)
    command_transaction_success = BooleanField(default=False)


class Relationship(BaseModel):
    from_product = ForeignKeyField(ProductDb, backref='relationships')
    to_product = ForeignKeyField(ProductDb, backref='related_to')

    class Meta:
        indexes = (
            (('from_product', 'to_product'), True),
        )


def get_database_location():
    print("init-db")
    create_tables()


def create_tables():
    with database:
        database.create_tables([ProductDb, CommandDb])
