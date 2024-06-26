import random
import requests
import json
from HandleException import *
from database import database, get_database_location
from peewee import fn
import click
from flask import Flask, render_template, request, redirect, abort, make_response, jsonify
from urllib.request import urlopen, Request
from urllib.parse import urlencode
import os
import ast
import redis

database.connect()
cache = redis.from_url(url=os.environ.get("REDIS_URL"))


class Product:
    def __init__(self, id, quantite):
        self.id = id
        self.quantite = quantite


products_list = []

app = Flask(__name__)


@click.command("initialisation_bd")
def initialisation_bd():
    database_path = get_database_location()


def app_initialisation(application):
    application.cli.add_command(initialisation_bd)


app_initialisation(app)


def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client


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
                desc = product['description']
                string_null = "\x00"
                if string_null in desc:
                    desc = desc.rstrip(string_null)
                ProductDb.insert(
                    product_id=product['id'],
                    product_name=product['name'],
                    product_type=product['type'],
                    product_desc=desc,
                    product_image=product['image'],
                    product_weight=product['weight'],
                    product_height=product['height'],
                    product_price=product['price'],
                    product_in_stock=product['in_stock']
                ).execute()
    return render_template("index.html", products=products_list, order_id=get_order_id(), order_size=0)


@app.route("/order/<int:order_id>/shipping/", methods=['GET', 'POST'])
def initialize_order(order_id):
    if request.method == 'POST':
        order_size = request.form.get("order_size")
        print("order_size: " + str(order_size))
        products = []
        for x in range(1, int(order_size) + 1):
            item = request.form.get("input-item" + str(x))
            for product in products_list:
                if product['name'] == item:
                    item_id = product['id']
            quantity = request.form.get("input-quantite" + str(x))
            product = Product(int(item_id), int(quantity))
            validation = json.loads(product_validation(product))
            if validation["http_code"] == 200:
                print(str(validation))
                print("product : " + str(product))
                products.append(product)
            else:
                error = make_response(validation["http_name"] + " (" + validation["code"] + ") : " + validation["name"])
                abort(error)
        command = '{ "order": ['
        compteur = 0
        size = len(products)
        print(f"size : {size}")
        for p in products:
            compteur = compteur + 1
            command = command + '{"id": ' + str(p.id) + ' , "quantity": ' + str(p.quantite) + '}'
            if compteur < size:
                command = command + ","
            else:
                command = command + ']}'
        command = json.loads(command)
        CommandDb.insert(
            command_id=order_id,
            command=command).execute()
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
    command_summary = None
    command_return = []
    command_string = None
    command_for_cache = []
    weight_tot = 0
    cost_tot = 0
    order_line = CommandDb.get_or_none(CommandDb.command_id == order_id)
    command = order_line.command
    # order_dict = json.loads(order)
    if order_line:
        if not order_line.command_paid:
            print("order : " + str(command))
            print("order type : " + str(type(command)))
            item = None
            for p in command["order"]:
                print(f"produit : {str(p)}")
                pid = p["id"]
                p_quantity = p["quantity"]
                item = ProductDb.get_or_none(ProductDb.product_id == pid)
                command_return.append((item.product_name, item.product_desc, p_quantity))
                command_string = [{"name": item[0], "desc": item[1], "quantity": item[2]} for item in command_return]
                if item:
                    p_cost = item.product_price * p_quantity
                    cost_tot = cost_tot + p_cost
                    weight = item.product_weight * p_quantity
                    weight_tot = weight_tot + weight
            cost_tot = round(cost_tot, 2)
            print(f"command_return : {command_return}")
            if item:
                expedition_price = 0
                if weight_tot >= 2000:
                    expedition_price = 25
                elif 500 <= weight_tot < 2000:
                    expedition_price = 10
                elif weight_tot < 500:
                    expedition_price = 5
                card_info = request.form.to_dict()
                print("Card info : " + str(card_info))
                input_name = card_info["name"]
                input_number = card_info["number"]
                input_exp_year = int(card_info["exp_year"])

                if card_info["exp_year"] == "":
                    input_exp_year = 0

                input_exp_month = int(card_info["exp_month"])
                if card_info["exp_month"] == "":
                    input_exp_month = 0

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
                        "amount_charged": int(cost_tot + expedition_price)
                    }

                    print(str(card_info_to_send))
                    url = "http://dimprojetu.uqac.ca/~jgnault/shops/pay/"
                    headers = {"Content-Type": "application/json"}
                    response = requests.post(url, json=card_info_to_send, headers=headers).text
                    response_json = json.loads(response)
                    print(f"reponse : {str(response_json)}")
                    order = CommandDb.get_or_none(order_id)
                    order.command_paid = True
                    order.command_amount_charged = response_json["transaction"]["amount_charged"]
                    order.command_transaction_id = response_json["transaction"]["id"]
                    order.command_transaction_success = response_json["transaction"]["success"]
                    order.save()
                    print(f"command_string : {command_string}")
                    print(f"command_string type : {type(command_string)}")
                    command_summary = {
                        "order": {
                            "items": command_string,
                            "shipping_info": {
                                "country": order.command_country,
                                "address": order.command_address,
                                "postal_code": order.command_postal_code,
                                "city": order.command_city,
                                "province": order.command_province
                            },
                            "email": order.command_email,
                            "total_price": cost_tot,
                            "paid": order.command_paid,
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
                    # command_summary["order"]["items"] = json.loads(command_json)
                    print(f"command summary :{str(command_summary)}")
                    command_for_cache = str(command_summary)
                    cache.set(order_id, command_for_cache)
                else:
                    error = make_response(validation["http_name"] + " (" + validation["code"] + ") : " + validation["name"])
                    abort(error)
        else:
            command_from_cache = ast.literal_eval(cache.get(order_id).decode('utf-8'))
            return render_template("confirmation.html", command_summary=command_from_cache)
    else:
        error = make_response(404, "La commande recherchée n'existe pas")
        abort(error)
    return render_template("confirmation.html", command_summary=command_summary)


@app.route("/order/<int:order_id>/", methods=['GET'])
def get_order(order_id):
    order_line = CommandDb.get_or_none(CommandDb.command_id == order_id)
    if order_line:
        if order_line.command_paid:
            command_from_cache = ast.literal_eval(cache.get(order_id).decode('utf-8'))
            return render_template("confirmation.html", command_summary=command_from_cache)
    else:
        error = make_response(404, "La commande recherchée n'existe pas")
        abort(error)


database.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
