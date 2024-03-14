from peewee import *
import os

database = SqliteDatabase("database.db")


class BaseModel(Model):
    class Meta:
        database = database


class ProductDb(BaseModel):
    product_id = IntegerField(unique=True)
    product_name = CharField()
    product_type = CharField()
    product_in_stock = BooleanField()
    product_desc = CharField()
    product_price = FloatField()
    product_height = FloatField()
    product_weight = FloatField()
    product_image = CharField()


class CommandDb(BaseModel):
    command_id = AutoField(unique=True)
    command_product_id = ForeignKeyField(ProductDb, backref='product_id')
    command_quantity = IntegerField()
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
    return os.environ.get("database", "database.db")


def create_tables():
    with database:
        database.create_tables([ProductDb, CommandDb, Relationship])
