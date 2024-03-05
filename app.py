import requests
import json
from flask import Flask
app = Flask(__name__)


@app.route('/shops/products/')
def get_products():
    return requests.get('/http://dimprojetu.uqac.ca/~jgnault/shops/products/').content

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
    products = json.dumps(get_products())
    print(products)
