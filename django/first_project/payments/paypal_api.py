# paypal_api.py
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

def get_paypal_access_token():
    """Lấy OAuth2 token từ PayPal sandbox/live"""
    url = f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token"
    data = {'grant_type': 'client_credentials'}
    response = requests.post(url, data=data,
                             auth=HTTPBasicAuth(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET))
    response.raise_for_status()
    return response.json().get("access_token")


def create_paypal_order(amount_str, return_url, cancel_url, currency="USD", access_token=None):
    """Tạo PayPal order, trả về JSON response"""
    if access_token is None:
        access_token = get_paypal_access_token()

    url = f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {"amount": {"currency_code": currency, "value": str(amount_str)}}  # chuỗi chuẩn
        ],
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def capture_paypal_order(order_id, access_token=None):
    """Capture order PayPal sau khi người dùng approve"""
    if access_token is None:
        access_token = get_paypal_access_token()
    url = f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders/{order_id}/capture"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()
