import random

import requests
import json
from peewee import *

from flask import Flask, render_template, request, redirect, abort
from urllib.request import urlopen

database = SqliteDatabase("database.db")

database.connect()


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


class Relationship(BaseModel):
    from_product = ForeignKeyField(ProductDb, backref='relationships')
    to_product = ForeignKeyField(ProductDb, backref='related_to')

    class Meta:
        indexes = (
            (('from_product', 'to_product'), True),
        )


def create_tables():
    with database:
        database.create_tables([ProductDb, CommandDb, Relationship])


class Product:
    def __init__(self, id, quantite):
        self.id = id
        self.quantite = quantite


products_list = []

database.create_tables([ProductDb, CommandDb])

app = Flask(__name__)


@app.route('/')
@app.route('/home')
def home():  # put application's code here
    return render_template("index.html")


@app.route("/result", methods=["GET"])
def get_products():
    with urlopen("http://dimprojetu.uqac.ca/~jgnault/shops/products/") as response:
        products_json = json.loads(response.read())
        #   print(products_json)
        for product in products_json['products']:
            product_data = {
                "id": product['id'],
                "name": product['name'],
                "type": product['type'],
                "description": product['description'],
                "image": product['image'],
                "height": product['height'],
                "weight": product['weight'],
                "price": product['price'],
                "in_stock": product['in_stock']
            }
            products_list.append(product_data)
            #   print("Product id : " + str(product['id']))
            #   print("Product id type : " + str(type(product['id'])))
            searched_product = ProductDb.get_or_none(product['id'])
            #   print("Searched Product : " + str(searched_product))
            if searched_product is None:
                #   On ajoute seulement si le produit n'existe pas dans la bd
                ProductDb.insert(
                    product_id=product['id'],
                    product_name=product['name'],
                    product_type=product['type'],
                    product_desc=product['description'],
                    product_image=product['image'],
                    product_weight=product['weight'],
                    product_height=product['height'],
                    product_price=product['price'],
                    product_in_stock=product['in_stock']
                ).execute()

    return render_template("index.html", products=products_list)


@app.route("/order/<int:order_id>", methods=['GET', 'POST'])
def initialize_order(order_id):
    if request.method == 'POST':
        id_item = None
        for produit in products_list:
            if produit['id'] == eval(request.form.get('choix'))['id']:
                id_item = produit['id']
        product = Product(id_item, request.form.get('quantite'))
        order = {"product": {"id": product.id, "quantity": product.quantite}}
        print("Commande : " + str(order))
        print("type : " + str(type(order)))
        print("id : " + str(order['product']['id']))
        print("quantity : " + str(order['product']['quantity']))
        if CommandDb.select(fn.Max(CommandDb.command_id)).scalar() is None:
            order_id = 1
        else:
            order_id = CommandDb.select(fn.Max(CommandDb.command_id)).scalar() + 1
        print("next value : " + str(order_id))
        CommandDb.insert(
            command_id=order_id,
            command_product_id=order['product']['id'],
            command_quantity=order['product']['quantity']
        ).execute()
    return render_template("order.html", order_id=order_id)


@app.route("/order/<int:order_id>", methods=['GET', 'POST'])
def make_order(order_id):
    if request.method == 'POST':
        shipping_info = request.form.to_dict()
        print(type(shipping_info))
        print("SHIPPING INFO : " + str(shipping_info))
        method = shipping_info["method"]
        input_email = shipping_info["email"]
        input_contry = shipping_info["country"]
        input_address = shipping_info["address"]
        input_postal_code = shipping_info["postal_code"]
        input_city = shipping_info["city"]
        input_province = shipping_info["province"]


if __name__ == '__main__':
    app.run(debug=True, port=5000)
