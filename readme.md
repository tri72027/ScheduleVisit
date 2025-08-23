# Booking Automation App

Ứng dụng Python tự động đặt lịch hẹn tại trang [inpol.mazowieckie.pl](https://inpol.mazowieckie.pl)  
Có giao diện đơn giản bằng **Tkinter**, log hiển thị trực tiếp trong GUI và ghi ra file `app.log`.

---

## 🚀 Tính năng
- Đăng nhập nhiều tài khoản từ file `accounts.txt`
- Tự động duyệt case, chọn location & queue
- Xử lý calendar, chọn ngày & giờ khả dụng
- Log vừa hiển thị trong giao diện, vừa lưu vào `app.log`
- Có thể build thành `.exe` (Windows) hoặc `.dmg` (macOS)

---

## 📂 Cấu trúc project
project/
│── gui.py # Giao diện Tkinter
│── main.py # Luồng chính
│── browser.py # Khởi tạo Chrome
│── login.py # Đăng nhập
│── progress.py # Xử lý case & calendar
│── utils.py # Hàm tiện ích
│── config.py # Config chung (URL, file account...)
│── logger.py # Cấu hình logging
│── accounts.txt # Danh sách tài khoản (user|password)
│── requirements.txt
│── README.md


---

## ⚙️ Cài đặt môi trường

### 1. Tạo môi trường ảo (venv)
Khuyến nghị sử dụng `venv` để tránh xung đột thư viện.

```bash
python -m venv venv
```
2. Kích hoạt venv
Windows:

```bash
venv\Scripts\activate
```
Mac/Linux:
```bash
source venv/bin/activate
```
Khi kích hoạt thành công, terminal sẽ hiển thị (venv) ở đầu dòng.

3. Cài dependencies
```bash
pip install -r requirements.txt
```
▶️ Chạy ứng dụng
```bash
python gui.py
```
Nhập số ngày tối đa muốn quét, nhấn Bắt đầu.

Log sẽ hiển thị ngay trong cửa sổ GUI và được lưu vào app.log.

