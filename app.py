import requests
import json

from flask import Flask, render_template, request, redirect
from urllib.request import urlopen

app = Flask(__name__)


@app.route('/')
@app.route('/home')
def home():  # put application's code here
    return render_template("index.html")


@app.route("/result", methods=["GET"])
def get_products():
    with urlopen("http://dimprojetu.uqac.ca/~jgnault/shops/products/") as response:
        products = response.read()

    return render_template("index.html", products=products)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
