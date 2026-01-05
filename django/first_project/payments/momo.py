import json
import uuid
import requests
import hmac
import hashlib

# Thông tin môi trường MoMo
endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
partnerCode = "MOMO"
accessKey = "F8BBA842ECF85"
secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"

def create_momo_payment(amount, order_info, redirect_url, ipn_url):
    """
    Tạo giao dịch MoMo
    :param amount: Tổng số tiền thanh toán (Integer)
    :param order_info: Thông tin đơn hàng
    :param redirect_url: URL người dùng sau thanh toán
    :param ipn_url: URL nhận thông báo IPN từ MoMo (Webhook)
    :return: Phản hồi JSON từ MoMo API
    """
    # Chuyển số tiền về chuỗi số nguyên
    amount = str(int(amount))  # Đảm bảo gửi đúng định dạng

    # Tạo thông tin giao dịch MoMo
    order_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    request_type = "captureWallet"
    extra_data = ""

    # Tạo rawSignature theo định dạng MoMo
    raw_signature = (
        f"accessKey={accessKey}&amount={amount}&extraData={extra_data}"
        f"&ipnUrl={ipn_url}&orderId={order_id}&orderInfo={order_info}"
        f"&partnerCode={partnerCode}&redirectUrl={redirect_url}"
        f"&requestId={request_id}&requestType={request_type}"
    )

    # Tạo chữ ký HMAC SHA256
    h = hmac.new(bytes(secretKey, 'utf-8'), bytes(raw_signature, 'utf-8'), hashlib.sha256)
    signature = h.hexdigest()

    # Tạo payload gửi đến MoMo
    payload = {
        'partnerCode': partnerCode,
        'partnerName': "Test",
        'storeId': "MomoTestStore",
        'requestId': request_id,
        'amount': amount,
        'orderId': order_id,
        'orderInfo': order_info,
        'redirectUrl': redirect_url,
        'ipnUrl': ipn_url,
        'lang': "vi",
        'extraData': extra_data,
        'requestType': request_type,
        'signature': signature,
    }

    # Gửi request POST đến MoMo API
    response = requests.post(endpoint, json=payload, headers={'Content-Type': 'application/json'})

    # Xử lý phản hồi từ MoMo
    try:
        res = response.json()
        print("Phản hồi từ MoMo:", res)
        if res.get("resultCode") != 0:  # Check mã lỗi từ MoMo
            raise Exception(f"Lỗi từ MoMo: {res.get('message')}")
        return res  # Trả về JSON chứa payUrl
    except Exception as e:
        print(f"Lỗi khi gửi request tới MoMo: {e}")
        raise e