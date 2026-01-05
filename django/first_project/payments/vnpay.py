import hashlib
import hmac
import urllib.parse
from datetime import datetime
from django.conf import settings

def hmac_sha512(key, data):
    return hmac.new(key.encode(), data.encode(), hashlib.sha512).hexdigest()

def create_vnpay_url(order_id, amount, return_url):
    vnp_url = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
    tmn_code = settings.VNPAY_TMN_CODE
    hash_secret = settings.VNPAY_HASH_SECRET

    vnp_params = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": tmn_code,
        "vnp_Amount": int(amount * 100),
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": str(order_id),
        "vnp_OrderInfo": f"Thanh toan don hang #{order_id}",
        "vnp_OrderType": "other",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": return_url,
        "vnp_IpAddr": "127.0.0.1",
        "vnp_CreateDate": datetime.now().strftime('%Y%m%d%H%M%S'),
    }

    sorted_params = sorted(vnp_params.items())
    query = urllib.parse.urlencode(sorted_params)

    secure_hash = hmac_sha512(hash_secret, query)

    return f"{vnp_url}?{query}&vnp_SecureHash={secure_hash}"
