import random
import requests
import json
from HandleException import *
from database import database
from peewee import fn
from flask import Flask, render_template, request, redirect, abort, make_response, jsonify
from urllib.request import urlopen, Request
from urllib.parse import urlencode

database.connect()


class Product:
    def __init__(self, id, quantite):
        self.id = id
        self.quantite = quantite


products_list = []

database.create_tables([ProductDb, CommandDb])

app = Flask(__name__)


def get_order_id():
    if CommandDb.select(fn.Max(CommandDb.command_id)).scalar() is None:
        order_id = 1
    else:
        order_id = CommandDb.select(fn.Max(CommandDb.command_id)).scalar() + 1
    return order_id


@app.route('/', methods=['GET', 'POST'])
def home():
    with urlopen("http://dimprojetu.uqac.ca/~jgnault/shops/products/") as response:
        products_json = json.loads(response.read())
        print(str(products_json))
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
            searched_product = ProductDb.get_or_none(product['id'])
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
    return render_template("index.html", products=products_list, order_id=get_order_id())


@app.route("/order/<int:order_id>/shipping/", methods=['GET', 'POST'])
def initialize_order(order_id):
    if request.method == 'POST':
        id_item = None
        for produit in products_list:
            if produit['id'] == eval(request.form.get('choix'))['id']:
                id_item = produit['id']
        quantity = request.form.get('quantite')
        print("quantity : " + quantity)
        if quantity == "":
            quantity = 0
        product = Product(id_item, int(quantity))
        validation = json.loads(product_validation(product))
        if validation["http_code"] == 200:
            print(str(validation))
            order = {"product": {"id": product.id, "quantity": product.quantite}}
            print("Commande : " + str(order))
            print("type : " + str(type(order)))
            print("id : " + str(order['product']['id']))
            print("quantity : " + str(order['product']['quantity']))
            order_id = get_order_id()
            print("next value : " + str(order_id))
            CommandDb.insert(
                command_id=order_id,
                command_product_id=order['product']['id'],
                command_quantity=order['product']['quantity']
            ).execute()
        else:
            error = make_response(validation["http_name"] + " (" + validation["code"] + ") : " + validation["name"])
            abort(error)
    return render_template("order.html", order_id=order_id)


@app.route("/order/<int:order_id>/card_info/", methods=['GET', 'POST'])
def make_order(order_id):
    if request.method == 'POST':
        shipping_info = request.form.to_dict()
        print(type(shipping_info))
        print("SHIPPING INFO : " + str(shipping_info))
        input_email = shipping_info["email"]
        input_country = shipping_info["country"]
        input_address = shipping_info["address"]
        input_postal_code = shipping_info["postal_code"]
        input_city = shipping_info["city"]
        input_province = shipping_info["province"]

        validation = json.loads(order_validation(order_id, shipping_info))
        if validation["http_code"] == 200:
            print(str(validation))
            command = CommandDb.get_or_none(order_id)
            if command is not None:
                command.command_email = input_email
                command.command_country = input_country
                command.command_address = input_address
                command.command_postal_code = input_postal_code
                command.command_city = input_city
                command.command_province = input_province
                command.save()
        else:
            error = make_response(validation["http_name"] + " (" + validation["code"] + ") : " + validation["name"])
            abort(error)
    return render_template("card_info.html", order_id=order_id)


@app.route("/order/<int:order_id>/resume/", methods=['GET', 'POST'])
def order_details(order_id):
    if request.method == 'POST':
        order = CommandDb.get_or_none(order_id)
        item = ProductDb.get_or_none(order.command_product_id)
        weight = item.product_weight * order.command_quantity
        expedition_price = 0
        if weight >= 2000:
            expedition_price = 25
        elif 500 <= weight < 2000:
            expedition_price = 10
        elif weight < 500:
            expedition_price = 5
        card_info = request.form.to_dict()
        print("Card info : " + str(card_info))
        input_name = card_info["name"]
        input_number = card_info["number"]
        if card_info["exp_year"] == "":
            input_exp_year = 0
        else:
            input_exp_year = int(card_info["exp_year"])
        if card_info["exp_month"] == "":
            input_exp_month = 0
        else:
            input_exp_month = int(card_info["exp_month"])
        input_cvv = card_info["cvv"]

        validation = json.loads(validation_carte(input_name, input_number, input_exp_year, input_exp_month, input_cvv, order_id))
        if validation["http_code"] == 200:
            card_info_to_send = {
                "credit_card": {
                    "name": input_name,
                    "number": input_number,
                    "expiration_year": input_exp_year,
                    "cvv": input_cvv,
                    "expiration_month": input_exp_month
                },
                "amount_charged": int((order.command_quantity * item.product_price) + expedition_price)
            }

            print(str(card_info_to_send))
            url = "http://dimprojetu.uqac.ca/~jgnault/shops/pay/"
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json=card_info_to_send, headers=headers).text
            response_json = json.loads(response)
            print(str(response_json))
            order = CommandDb.get_or_none(order_id)
            if order is not None:
                order.command_paid = True
                order.command_amount_charged = response_json["transaction"]["amount_charged"]
                order.command_transaction_id = response_json["transaction"]["id"]
                order.command_transaction_success = response_json["transaction"]["success"]
                order.save()
            item = ProductDb.get_or_none(order.command_product_id)

            command_summary = {
                "order": {
                    "shipping_info": {
                        "country": order.command_country,
                        "address": order.command_address,
                        "postal_code": order.command_postal_code,
                        "city": order.command_city,
                        "province": order.command_province
                    },
                    "email": order.command_email,
                    "total_price": order.command_quantity * item.product_price,
                    "paid": order.command_paid,
                    "product": {
                        "id": item.product_id,
                        "quantity": order.command_quantity
                    },
                    "credit_card": {
                        "name": response_json["credit_card"]["name"],
                        "first_digits": response_json["credit_card"]["first_digits"],
                        "last_digits": response_json["credit_card"]["last_digits"],
                        "expiration_year": response_json["credit_card"]["expiration_year"],
                        "expiration_month": response_json["credit_card"]["expiration_month"]
                    },
                    "transaction": {
                        "id": order.command_transaction_id,
                        "success": order.command_transaction_success,
                        "amount_charged": order.command_amount_charged
                    },
                    "shipping_price": expedition_price,
                    "id": order_id
                }
            }
            print(str(command_summary))
        else:
            error = make_response(validation["http_name"] + " (" + validation["code"] + ") : " + validation["name"])
            abort(error)
    return render_template("confirmation.html")


database.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
