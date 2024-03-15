from app import *
import pytest


def test_home_code_ok(client):
    response = client.get('/')
    assert response.status_code == 200


def test_shipping_should_code_ok(client):
    response = client.get('/order/<int:order_id>/shipping/')
    assert response.status_code == 200


def test_credit_should_code_ok(client):
    response = client.get('/order/<int:order_id>/card_info/')
    assert response.status_code == 200


def test_resume_code_ok(client):
    response = client.get('/order/<int:order_id>/resume/')
    assert response.status_code == 200


def test_order_code_zero(client):
    id = 0
    response = client.post('/order/<int:order_id>/shipping/', data = {'order_id': id})
    data = response.data.decode()
    assert data == "Order code"


def test_order_code_none(client):
    id = None
    response = client.post('/order/<int:order_id>/shipping/', data = {'order_id': id})
    data = response.data.decode()
    assert data == "Order code"
