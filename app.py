"""
app.py — Server Flask cho Masterclass Landing Page
Chức năng:
  - GET  /              : Trang landing page chính
  - POST /checkout      : Nhận form đăng ký, tạo đơn hàng, hiển thị QR Sepay
  - POST /webhook/sepay : Nhận thông báo thanh toán từ Sepay (webhook)
  - GET  /admin         : Trang quản trị xem đơn hàng

Chạy: python app.py
"""

import sqlite3
import os
import json
import hmac
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for

app = Flask(__name__, template_folder="templates", static_folder=".")

# ── Cấu hình ──────────────────────────────────────────────────────
DB_PATH       = os.path.join(os.path.dirname(__file__), "brain.db")
PRODUCT_PRICE = 499000          # VNĐ — giá ưu đãi sớm

# !! Thay bằng thông tin tài khoản Sepay thật của bạn !!
SEPAY_ACCOUNT_NUMBER = "0030100065507004"   # So tai khoan OCB
SEPAY_BANK_CODE      = "OCB"                 # Ma ngan hang OCB
SEPAY_WEBHOOK_SECRET = ""                    # API Secret tu trang Sepay (dien sau)

# ── Helper DB ─────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def gen_order_code():
    """Tạo mã đơn hàng duy nhất, ví dụ: MC250502001"""
    prefix = "MC" + datetime.now().strftime("%y%m%d")
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    db.close()
    return f"{prefix}{count+1:03d}"

# ── Routes ────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve trang landing page chính"""
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    """Serve các file tĩnh (CSS, JS, ảnh)"""
    return send_from_directory(".", filename)


@app.route("/checkout", methods=["POST"])
def checkout():
    """
    Nhận thông tin khách từ form, tạo đơn hàng + trả về QR thanh toán Sepay.
    Body JSON: { name, phone, email }
    """
    data = request.get_json(force=True)
    name  = (data.get("name")  or "").strip()
    phone = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip()

    if not name or not phone:
        return jsonify({"ok": False, "error": "Vui lòng điền đủ Tên và Số điện thoại."}), 400

    db = get_db()
    try:
        # Lưu khách hàng
        cur = db.execute(
            "INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)",
            (name, phone, email)
        )
        customer_id = cur.lastrowid

        # Lấy product_id
        product = db.execute("SELECT id FROM products WHERE active=1 LIMIT 1").fetchone()
        product_id = product["id"] if product else 1

        # Tạo mã đơn
        order_code = gen_order_code()

        # Lưu đơn hàng
        db.execute(
            "INSERT INTO orders (order_code, customer_id, product_id, amount, status) VALUES (?,?,?,?,?)",
            (order_code, customer_id, product_id, PRODUCT_PRICE, "pending")
        )
        db.commit()
    finally:
        db.close()

    # Tạo link QR Sepay VietQR
    # Cú pháp nội dung chuyển khoản: Mã đơn hàng (để Sepay nhận diện tự động)
    transfer_content = order_code
    amount_str = str(PRODUCT_PRICE)

    # Dùng VietQR API public để hiển thị QR (không cần API key)
    qr_url = (
        f"https://img.vietqr.io/image/"
        f"{SEPAY_BANK_CODE}-{SEPAY_ACCOUNT_NUMBER}-compact2.png"
        f"?amount={amount_str}"
        f"&addInfo={transfer_content}"
        f"&accountName=NGUYEN+THI+VIET+PHUONG"
    )

    return jsonify({
        "ok":           True,
        "order_code":   order_code,
        "amount":       PRODUCT_PRICE,
        "qr_url":       qr_url,
        "bank_code":    SEPAY_BANK_CODE,
        "account":      SEPAY_ACCOUNT_NUMBER,
        "content":      transfer_content,
    })


@app.route("/webhook/sepay", methods=["POST"])
def sepay_webhook():
    """
    Nhận thông báo thanh toán từ Sepay.
    Sepay sẽ POST vào đây mỗi khi có giao dịch khớp.
    """
    payload = request.get_json(force=True)
    print(f"[Webhook Sepay] Nhan duoc: {json.dumps(payload, ensure_ascii=True)}")

    # Lấy nội dung chuyển khoản (chứa order_code)
    content    = payload.get("content", "") or payload.get("description", "")
    amount     = payload.get("transferAmount", 0) or payload.get("amount", 0)
    sepay_ref  = payload.get("referenceCode", "") or payload.get("id", "")

    # Tìm mã đơn trong nội dung
    db = get_db()
    try:
        orders = db.execute(
            "SELECT id, order_code, amount, status FROM orders WHERE status='pending'"
        ).fetchall()

        matched = None
        for order in orders:
            if order["order_code"] in content:
                matched = order
                break

        if not matched:
            print(f"[Webhook] Khong khop don nao trong noi dung: {content}")
            return jsonify({"success": True})  # Tra 200 de Sepay khong retry

        # CHE DO TEST: Cho phep so tien bat ky tu 2000d tro len
        # Sau khi test xong, doi lai: if int(amount) < matched["amount"]:
        if int(amount) < 2000:
            print(f"[Webhook] So tien qua nho de test: {amount}")
            return jsonify({"success": True})

        # Xác nhận thanh toán thành công!
        db.execute(
            "UPDATE orders SET status='paid', paid_at=?, sepay_ref=? WHERE id=?",
            (datetime.now().isoformat(), str(sepay_ref), matched["id"])
        )
        db.commit()
        print(f"[Webhook] THANH CONG! Don {matched['order_code']} da duoc thanh toan!")

    finally:
        db.close()

    return jsonify({"success": True})


@app.route("/admin")
def admin():
    """Trang quản trị xem danh sách đơn hàng"""
    db = get_db()
    orders = db.execute("""
        SELECT
            o.order_code,
            o.amount,
            o.status,
            o.created_at,
            o.paid_at,
            c.name   AS customer_name,
            c.phone  AS customer_phone,
            c.email  AS customer_email
        FROM orders o
        LEFT JOIN customers c ON c.id = o.customer_id
        ORDER BY o.created_at DESC
    """).fetchall()

    stats = db.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) as paid,
            SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status='paid' THEN amount ELSE 0 END) as revenue
        FROM orders
    """).fetchone()
    db.close()

    return render_template("admin.html", orders=orders, stats=stats)


@app.route("/api/order-status/<order_code>")
def order_status(order_code):
    """Polling endpoint: trang web gọi mỗi 3s để kiểm tra đơn đã thanh toán chưa"""
    db = get_db()
    order = db.execute(
        "SELECT status, paid_at FROM orders WHERE order_code=?", (order_code,)
    ).fetchone()
    db.close()

    if not order:
        return jsonify({"status": "not_found"})
    return jsonify({"status": order["status"], "paid_at": order["paid_at"]})


# ── Run ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  [OK] Masterclass Backend Server dang chay")
    print("  Trang web : http://localhost:5000")
    print("  Admin     : http://localhost:5000/admin")
    print("  Nhan Ctrl+C de dung")
    print("=" * 50)
    app.run(debug=True, port=5000)
