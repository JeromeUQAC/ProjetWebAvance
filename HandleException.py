def handle_exception(http_code, http_name, code, name):
    response = e.get_response()
    response.date = json.dumps({
        "http_code": http_code,
        "http_name": http_name,
        "code": code,
        "name": name,
    })
    response.content_type = "application/json"
    return response


#   1 si id / quantity / product est vide
def product_validation(product):
    if product.id is None or product.quantity is None or object is None:
        handle_exception(422, "UnprocessableEntity", "missing-fields", "La création d'une commande nécéssite un produit")

    #   2 si le truc est en stock
    if not product_id.in_stock:
        handle_exception(422, "UnprocessableEntity", "out-of-inventory", "Le produit demandé n'est pas en inventaire")

    #   3 si commande n'existe pas
    handle_exception(404, "NotFound", "inexisting-command", "La commande n'existe pas")

    #   4 si manque des champs obligatoires shipping
    if (emails is None) or (shipping is None) or (shipping_information.country is None) or (
            shipping_information.postal_code is None) or (shipping_information.city is None) or (
            shipping_information.state.province is None):
        handle_exception(422, "UnprocessableEntity", "missing-fields", "Il manque un ou plusieurs champs qui sont obligatoires")


#   5 - 6 - 7 - 8
def validation_carte(numero, exp_annee, exp_mois, cvv, id):
    carte_ok = False
    date_ok = False
    cvv_ok = False
    id_ok = id  # Initiliser selon si la commande est déjà payée #Commande.paid

    if id_ok:  ##PUT /order/<int:order_id>
        handle_exception(422, "UnprocessableEntity", "already-paid", "La commande a déjà été payée")

    if numero == "4242 4242 4242 4242" or numero == "4000 0000 0000 0002":
        carte_ok = True
    if exp_annee < 2025 and exp_mois < 13:
        date_ok = True
    if len(cvv) == 3:
        cvv_ok = True
        try:
            int(cvv) / 2
        except ValueError:
            print("NO")
            cvv_ok = False
    if carte_ok and date_ok and cvv_ok:
        print("ok")
    else:
        if numero == "" or exp_annee == "" or exp_mois == "" or cvv == "":
            handle_exception(422, "UnprocessableEntity", "missing-fields",
                             "Les informations du client sont nécéssaires avant d'appliquer une carte de crédit")

        else:
            handle_exception(422, "UnprocessableEntity", "already-paid", "La carte de crédit a été déclinée")
