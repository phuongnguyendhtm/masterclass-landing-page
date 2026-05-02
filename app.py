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
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
import resend

load_dotenv()  # Doc cau hinh tu file .env

app = Flask(__name__, template_folder="templates", static_folder=".")

# ── Cấu hình (đọc từ file .env) ──────────────────────────────────
DB_PATH              = os.path.join(os.path.dirname(__file__), "brain.db")
PRODUCT_PRICE        = int(os.environ.get("PRODUCT_PRICE", 499000))
SEPAY_ACCOUNT_NUMBER = os.environ.get("SEPAY_ACCOUNT_NUMBER", "0030100065507004")
SEPAY_BANK_CODE      = os.environ.get("SEPAY_BANK_CODE", "OCB")
SEPAY_WEBHOOK_SECRET = os.environ.get("SEPAY_WEBHOOK_SECRET", "")

resend.api_key       = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM          = os.environ.get("RESEND_FROM", "onboarding@resend.dev")
RESEND_TO_TEST       = os.environ.get("RESEND_TO_TEST", "")


def send_email(to_email, subject, html_body):
    """Gui email qua Resend. Neu chua co domain thi chi gui ve to_email cua chinh minh."""
    if not resend.api_key:
        print("[Email] Chua co API Key — bo qua.")
        return
    # Resend mien phi chi cho phep gui den email da xac minh (khong co custom domain)
    # Neu chua verify domain, gui ve email cua chinh minh de test
    actual_to = RESEND_TO_TEST if RESEND_TO_TEST else to_email
    try:
        params = {
            "from": RESEND_FROM,
            "to": [actual_to],
            "subject": subject,
            "html": html_body,
        }
        r = resend.Emails.send(params)
        print(f"[Email] Gui thanh cong den {actual_to} — ID: {r.get('id','')}")
    except Exception as e:
        print(f"[Email] Loi: {e}")


def send_welcome_email(name, email, order_code):
    subject = f"Chao {name} — Toi vua giu cho cho ban"
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
      <h2 style="color:#00A86B">{name} oi,</h2>
      <p>Cam on ban da dang ky <strong>Masterclass: He Thong AI Marketing Tinh Gon</strong>.</p>
      <p>Toi da giu cho cho ban roi — ma don: <strong style="color:#00A86B">{order_code}</strong></p>
      <p>5 tuan, moi tuan ban se co 1 he thong chay that tren may tinh cua ban.<br>
      Tuan 1 xong la ban co website + chatbot.<br>
      Tuan 5 xong la co may ban hang tu dong 24/7 — khong can thue nhan su.</p>
      <p>Neu ban chua chuyen khoan, hay hoan tat thanh toan de chot suat.<br>
      Neu da chuyen roi — toi se lien he ban qua SDT trong vong 24 gio.</p>
      <p>Bat ky cau hoi nao cu reply email nay — toi doc het.</p>
      <p>Phuong</p>
    </div>
    """
    send_email(email, subject, html)


def send_nurture_email(name, email):
    subject = "Tai sao 90% nguoi lam marketing van ton 3 gio/ngay cho viec co the tu dong hoa"
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
      <h2 style="color:#00A86B">{name} oi,</h2>
      <p>Hom nay khong ban gi — toi muon chia se voi ban 1 dieu toi quan sat duoc.</p>
      <p>Phan lon chu doanh nghiep nho va solopreneur dang danh 3-4 gio moi ngay cho nhung viec nay:</p>
      <ul>
        <li>Tra loi tin nhan hoi gia</li>
        <li>Copy thong tin khach vao Excel</li>
        <li>Kiem tra ngan hang xem tien vao chua</li>
        <li>Viet caption dang bai mang xa hoi</li>
        <li>Nhan tin cham soc khach sau mua</li>
      </ul>
      <p>Van de khong phai la ho luoi. Ma la ho chua co he thong.</p>
      <p>Khi toi noi "AI Marketing Tinh Gon" — toi khong co nghia la dung ChatGPT de viet bai cho nhanh hon. Toi noi den viec xay mot he thong ma tung phan trong danh sach tren deu chay tu dong.</p>
      <p>Chatbot tra loi thay ban.<br>
      Form tu luu thong tin khach.<br>
      Ngan hang tu bao ve khi co tien.<br>
      Email tu cham soc khach theo lich.</p>
      <p>Ban chi can mo bao cao buoi sang va quyet dinh buoc tiep theo.</p>
      <p>Day la thu toi se giup ban xay trong 5 tuan.</p>
      <p>Phuong</p>
      <p><small>P.S. Neu ban chua giu cho, hom nay van con suat uu dai 499.000d — ngay mai toi chua chac giu duoc muc nay.</small></p>
    </div>
    """
    send_email(email, subject, html)


def send_closing_email(name, email):
    subject = "Con [X] suat — va day la ly do toi khong tang them sau do"
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
      <h2 style="color:#00A86B">{name} oi,</h2>
      <p>Toi se noi thang.</p>
      <p>Masterclass nay gioi han 15 nguoi — khong phai chieu marketing. Ma vi voi moi nguoi, toi can xem that su ho dang van hanh kieu gi, he thong nao phu hop, va di sat trong 5 tuan do.</p>
      <p>Qua 15 nguoi, toi khong lam duoc chuyen do nua.</p>
      <p>Muc gia 499.000d la muc danh cho nguoi dang ky som — nhung nguoi tin vao huong di nay truoc khi thay ket qua. Sau khi du 15 suat, toi se dong dang ky.</p>
      <p>Neu ban dang can nhac, day la nhung gi ban se co sau 5 tuan:</p>
      <ul>
        <li>Website + chatbot tu van tu dong</li>
        <li>He thong nhan thanh toan qua QR (khong can ngoi truc)</li>
        <li>CRM quan ly khach hang</li>
        <li>Email marketing tu dong cham soc</li>
        <li>Bo nao AI biet viet content theo dung giong ban</li>
      </ul>
      <p>Tat ca tren may tinh cua ban — khong phu thuoc vao nen tang nao.</p>
      <p>👉 Giu cho tai: <strong>http://localhost:5000</strong></p>
      <p>Neu ban co cau hoi gi truoc khi quyet dinh, cu reply email nay.</p>
      <p>Phuong</p>
    </div>
    """
    send_email(email, subject, html)


def send_confirmation_email(name, email, order_code, amount):
    subject = f"Da xac nhan — Chao mung ban vao Masterclass!"
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
      <h2 style="color:#00A86B">{name} oi,</h2>
      <p>Toi da nhan duoc thanh toan cua ban. Cho trong Masterclass da duoc xac nhan.</p>
      <div style="background:#f5f5f5;padding:16px;border-radius:8px;margin:16px 0">
        <p style="margin:4px 0"><strong>Khoa hoc:</strong> He Thong AI Marketing Tinh Gon (5 tuan)</p>
        <p style="margin:4px 0"><strong>So tien:</strong> {amount:,}d</p>
        <p style="margin:4px 0"><strong>Ma don:</strong> {order_code}</p>
      </div>
      <p><strong>Buoc tiep theo:</strong><br>
      Toi se lien he ban qua SDT da dang ky trong vong 24 gio de them ban vao nhom Zalo cua lop.</p>
      <p>Hen gap ban trong lop!</p>
      <p>Phuong</p>
    </div>
    """
    send_email(email, subject, html)


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

    # Gui email chao mung ngay sau khi tao don
    send_welcome_email(name, email, order_code)
    
    # Che do test: Gui luon ca 3 email neu email co chu +test
    if "+test" in email.lower():
        send_nurture_email(name, email)
        send_closing_email(name, email)

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

        # Gui email xac nhan don hang
        customer = get_db().execute(
            "SELECT name, email FROM customers WHERE id=?", (matched["customer_id"],)
        ).fetchone()
        if customer and customer["email"]:
            send_confirmation_email(
                customer["name"], customer["email"],
                matched["order_code"], matched["amount"]
            )

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
    port = int(os.environ.get("PORT", 3000))
    print("=" * 50)
    print("  [OK] Masterclass Backend Server dang chay")
    print(f"  Trang web : http://localhost:{port}")
    print(f"  Admin     : http://localhost:{port}/admin")
    print("  Nhan Ctrl+C de dung")
    print("=" * 50)
    app.run(host="0.0.0.0", debug=False, port=port)
