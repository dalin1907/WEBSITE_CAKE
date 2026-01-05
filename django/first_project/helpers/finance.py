from decimal import Decimal

def convert_to_vnd(amount):
    """
    Chuyển đổi giá trị từ Decimal (lưu trong database) sang số nguyên VNĐ (integer).
    """
    try:
        # Kiểm tra nếu đầu vào là Decimal
        if not isinstance(amount, Decimal):
            raise ValueError("Giá trị truyền vào không phải kiểu Decimal.")

        # Chuyển đổi số tiền: nhân với 1000 và ép kiểu integer (VNĐ)
        return int(amount * Decimal('1000'))  # Ví dụ: 20.000 -> 20000
    except (ValueError, TypeError) as e:
        raise ValueError(f"Lỗi khi chuyển đổi số tiền: {e}")