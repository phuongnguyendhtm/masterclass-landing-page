# Masterclass AI Marketing — Automation System

Hệ thống Landing Page, CRM, Thanh Toán, và Email Tự Động xây dựng bằng Python (Flask) và SQLite.

## Tính năng
- **Landing Page:** Trang giới thiệu dark mode hiện đại.
- **Checkout:** Điền form và hiển thị QR thanh toán tự động bằng VietQR.
- **Webhook:** Tích hợp Sepay để nhận thông báo chuyển khoản tự động và cập nhật trạng thái đơn hàng.
- **CRM/Admin:** Quản lý sản phẩm, danh sách đăng ký và đơn hàng tại `/admin`.
- **Email Automation:** Gắn Resend API để gửi email chào mừng, email nuôi dưỡng và xác nhận đơn hàng tự động.

## Cài đặt cục bộ (Local)

1. Tạo môi trường ảo (Khuyên dùng):
   ```bash
   python -m venv venv
   source venv/bin/activate  # (hoặc `venv\Scripts\activate` trên Windows)
   ```

2. Cài đặt thư viện:
   ```bash
   pip install -r requirements.txt
   ```

3. Cấu hình bảo mật:
   - Tạo file `sepay_config.txt` và điền: `SEPAY_WEBHOOK_SECRET=your_secret_key`
   - Tạo file `resend_config.txt` và điền: `RESEND_API_KEY=your_api_key`
   - Đảm bảo có sẵn `brain.db` hoặc chạy `setup_crm.py` để tạo.

4. Chạy server:
   ```bash
   python app.py
   ```
   Web sẽ chạy tại `http://localhost:5000`
