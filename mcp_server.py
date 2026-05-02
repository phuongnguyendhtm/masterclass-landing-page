"""
mcp_server.py — MCP Server cho Masterclass Landing Page
Cung cap 3 "nut bam" de AI Agent (GoClaw) co the thao tac vao database.

Chay: python mcp_server.py
Port: 3001 (chi lang nghe localhost, khong mo ra internet)
"""

import sqlite3
import os
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP

# Khoi tao MCP Server
mcp = FastMCP(
    "Masterclass Business Tools",
    host="127.0.0.1",
    port=3001
)

DB_PATH = os.path.join(os.path.dirname(__file__), "brain.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Tool 1: Bao cao don hang hom nay ──────────────────────────────
@mcp.tool()
def biz_report_today() -> str:
    """Bao cao don hang va doanh thu hom nay. Goi khi user hoi 'hom nay co don nao khong', 'bao cao doanh thu', 'tinh hinh kinh doanh'."""
    db = get_db()
    today = datetime.now().strftime("%Y-%m-%d")

    # Tong don hom nay
    orders = db.execute(
        "SELECT o.order_code, o.amount, o.status, o.created_at, c.name, c.phone "
        "FROM orders o LEFT JOIN customers c ON c.id = o.customer_id "
        "WHERE o.created_at LIKE ?", (f"{today}%",)
    ).fetchall()

    total_orders = len(orders)
    paid_orders = [o for o in orders if o["status"] == "paid"]
    pending_orders = [o for o in orders if o["status"] == "pending"]
    revenue = sum(o["amount"] for o in paid_orders)

    # Tong toan thoi gian
    all_stats = db.execute(
        "SELECT COUNT(*) as total, "
        "SUM(CASE WHEN status='paid' THEN amount ELSE 0 END) as total_revenue "
        "FROM orders"
    ).fetchone()

    db.close()

    report = f"📊 BAO CAO HOM NAY ({today}):\n"
    report += f"- Tong don: {total_orders}\n"
    report += f"- Da thanh toan: {len(paid_orders)} don\n"
    report += f"- Cho thanh toan: {len(pending_orders)} don\n"
    report += f"- Doanh thu hom nay: {revenue:,}d\n\n"

    if paid_orders:
        report += "Chi tiet don da thanh toan:\n"
        for o in paid_orders:
            report += f"  • {o['name']} - {o['amount']:,}d - Ma: {o['order_code']}\n"

    report += f"\n📈 TOAN THOI GIAN: {all_stats['total']} don, tong doanh thu {all_stats['total_revenue']:,}d"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] biz_report_today() called — {total_orders} orders today")

    return report


# ── Tool 2: Xem danh sach khach hang ──────────────────────────────
@mcp.tool()
def biz_list_customers(limit: int = 10) -> str:
    """Xem danh sach khach hang gan day. Goi khi user hoi 'khach hang moi', 'ai dang ky gan day', 'danh sach khach'."""
    db = get_db()

    customers = db.execute(
        "SELECT c.name, c.phone, c.email, c.note, c.created_at, "
        "COUNT(o.id) as order_count, "
        "SUM(CASE WHEN o.status='paid' THEN o.amount ELSE 0 END) as total_paid "
        "FROM customers c "
        "LEFT JOIN orders o ON o.customer_id = c.id "
        "GROUP BY c.id "
        "ORDER BY c.created_at DESC LIMIT ?", (limit,)
    ).fetchall()

    db.close()

    if not customers:
        return "Chua co khach hang nao trong he thong."

    result = f"👥 {len(customers)} KHACH HANG GAN NHAT:\n\n"
    for i, c in enumerate(customers, 1):
        result += f"{i}. {c['name']}\n"
        result += f"   📱 {c['phone'] or 'Chua co SĐT'}\n"
        result += f"   📧 {c['email'] or 'Chua co email'}\n"
        result += f"   🛒 {c['order_count']} don, da thanh toan: {c['total_paid']:,}d\n"
        if c['note']:
            result += f"   📝 Ghi chu: {c['note']}\n"
        result += f"   📅 Dang ky: {c['created_at']}\n\n"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] biz_list_customers(limit={limit}) called — {len(customers)} results")

    return result


# ── Tool 3: Cap nhat ghi chu khach hang ───────────────────────────
@mcp.tool()
def biz_update_customer_note(customer_name: str, note: str) -> str:
    """Cap nhat ghi chu cho khach hang (VIP, da goi dien, can follow up...). Goi khi user noi 'ghi chu khach A la VIP', 'them note cho khach B'."""
    db = get_db()

    # Tim khach hang theo ten (khong phan biet hoa thuong)
    customer = db.execute(
        "SELECT id, name, note FROM customers WHERE LOWER(name) LIKE LOWER(?)",
        (f"%{customer_name}%",)
    ).fetchone()

    if not customer:
        db.close()
        return f"❌ Khong tim thay khach hang ten '{customer_name}'. Hay thu lai voi ten chinh xac hon."

    # Cap nhat ghi chu (them vao cuoi neu da co ghi chu cu)
    old_note = customer["note"] or ""
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    new_note = f"{old_note}\n[{timestamp}] {note}".strip()

    db.execute(
        "UPDATE customers SET note=? WHERE id=?",
        (new_note, customer["id"])
    )
    db.commit()
    db.close()

    log_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{log_time}] biz_update_customer_note('{customer_name}', '{note}') — updated customer #{customer['id']}")

    return f"✅ Da cap nhat ghi chu cho {customer['name']}:\n📝 {new_note}"


# ── Chay server ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  MCP Server — Masterclass Business Tools")
    print("  Dang lang nghe tai: http://127.0.0.1:3001")
    print("  3 tools: biz_report_today, biz_list_customers, biz_update_customer_note")
    print("=" * 50)
    mcp.run(transport="streamable-http")
