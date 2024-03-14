from database import database, CommandDb, ProductDb
import datetime
import re
import json

database.connect()


def handle_exception(http_code, http_name, code, name):
    response = json.dumps({
        "http_code": http_code,
        "http_name": http_name,
        "code": code,
        "name": name,
    })
    return response


#   1 si id / quantity / product est vide
def product_validation(product):
    regex_quantite = r'^\d{1,4}$'
    if product is None or product.quantite is None or product.quantite < 1 or not re.fullmatch(regex_quantite, str(product.quantite)):
        response = handle_exception(422, "UnprocessableEntity", "missing-fields", "La création d'une commande nécéssite un produit")

    #   2 si le truc est en stock
    elif ProductDb.get_or_none(product.id).product_in_stock == 0:
        response = handle_exception(422, "UnprocessableEntity", "out-of-inventory", "Le produit demandé n'est pas en inventaire")

    else:
        response = handle_exception(200, "NOPROPLEM", "no-problem", "200 OK")
    return response


def order_validation(order_id, shipping_info):
    #   3 si commande n'existe pas
    if CommandDb.get_or_none(order_id) is None:
        response = handle_exception(404, "NotFound", "inexisting-command", "La commande n'existe pas")

    #   4 si manque des champs obligatoires shipping
    elif ((shipping_info["email"] == "") or (shipping_info["address"] == "") or (shipping_info["country"] == "")
          or (shipping_info["postal_code"] == "") or (shipping_info["city"] == "") or (shipping_info["province"] == "")):
        response = handle_exception(422, "UnprocessableEntity", "missing-fields", "Il manque un ou plusieurs champs qui sont obligatoires")
    else:
        response = handle_exception(200, "NOPROPLEM", "no-problem", "200 OK")
    return response


    #   5 - 6 - 7 - 8
def validation_carte(nom, numero, exp_annee, exp_mois, cvv, order_id):
    regex_carte = r'^(?:\d{4} ){3}\d{4}$'
    regex_cvv = r'^\d{3}$'
    regex_annee = r'^\d{4}$'
    regex_mois = r'^\d{1,2}$'
    if exp_annee == "":
        exp_annee = 0
    if exp_mois == "":
        exp_mois = 0
    carte_ok = False
    date_ok = False
    nom_ok = False
    cvv_ok = False
    today = datetime.date.today()
    print("Today : " + str(today))
    print("Today month: " + str(today.month))
    print("Today year: " + str(today.year))
    paid = CommandDb.get_or_none(order_id).command_paid
    response = None

    if paid:
        response = handle_exception(422, "UnprocessableEntity", "already-paid", "La commande a déjà été payée")

    if re.fullmatch(regex_carte, numero):
        carte_ok = True
    if exp_annee >= today.year and 13 > exp_mois >= today.month:
        date_ok = True
    if re.fullmatch(regex_cvv, cvv):
        cvv_ok = True
    if nom != "":
        nom_ok = True
    if nom_ok and carte_ok and date_ok and cvv_ok:
        response = handle_exception(200, "NOPROPLEM", "no-problem", "200 OK")
    else:
        if not nom_ok or not cvv_ok:
            response = handle_exception(422, "UnprocessableEntity", "missing-fields",
                             "Les informations du client sont nécéssaires avant d'appliquer une carte de crédit")
        elif not carte_ok:
            response = handle_exception(422, "UnprocessableEntity", "card_declined","La carte de crédit a été déclinée")
        elif not date_ok:
            response = handle_exception(422, "UnprocessableEntity", "card_expired", "La carte de crédit est expirée")
        else:
            response = handle_exception(422, "UnprocessableEntity", "card_declined", "La carte de crédit a été déclinée")
    return response


database.close()
