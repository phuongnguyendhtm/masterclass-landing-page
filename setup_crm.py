# -*- coding: utf-8 -*-
"""
Script nang cap brain.db - Them 3 bang CRM:
  - products  : danh sách sản phẩm/khóa học
  - customers : thông tin khách hàng đăng ký
  - orders    : đơn hàng và trạng thái thanh toán

Chạy 1 lần: python setup_crm.py
"""
import sqlite3
from datetime import datetime

DB_PATH = "brain.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ── 1. Bảng PRODUCTS ──────────────────────────────────────────────
cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT,
    price       INTEGER NOT NULL,   -- đơn vị: VND
    slots_total INTEGER DEFAULT 15,
    slots_left  INTEGER DEFAULT 15,
    active      INTEGER DEFAULT 1,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# Thêm sản phẩm mặc định nếu chưa có
cur.execute("SELECT COUNT(*) FROM products")
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO products (name, description, price, slots_total, slots_left)
        VALUES (
            'Masterclass: Hệ Thống AI Marketing Tinh Gọn',
            '5 tuần xây cỗ máy bán hàng tự động bằng 1 nhân sự. Không cần biết code.',
            499000,
            15,
            15
        )
    """)
    print("[OK] Da them san pham mac dinh.")

# ── 2. Bảng CUSTOMERS ─────────────────────────────────────────────
cur.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    phone       TEXT,
    email       TEXT,
    source      TEXT DEFAULT 'landing-page',  -- kênh đến từ đâu
    note        TEXT,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# ── 3. Bảng ORDERS ────────────────────────────────────────────────
cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code      TEXT UNIQUE NOT NULL,   -- mã đơn hàng (VD: ORD001)
    customer_id     INTEGER REFERENCES customers(id),
    product_id      INTEGER REFERENCES products(id),
    amount          INTEGER NOT NULL,       -- số tiền thực thu (VND)
    status          TEXT DEFAULT 'pending', -- pending | paid | refunded
    paid_at         TEXT,                   -- thời điểm xác nhận thanh toán
    sepay_ref       TEXT,                   -- mã giao dịch Sepay trả về
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("[OK] Nang cap brain.db thanh cong!")
print("   Cac bang da co: products, customers, orders")
print("   Buoc tiep theo: python app.py")
