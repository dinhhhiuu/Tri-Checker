
# Tri-Checker — Network Guide

## Hướng dẫn cài đặt & chạy

1. Cài Python 3.8+ (nên dùng Python 3.10 trở lên).
2. (Khuyến nghị) Tạo môi trường ảo:
	```bash
	python -m venv .venv
	# Windows:
	.venv\Scripts\activate
	# Linux/macOS:
	source .venv/bin/activate
	```
3. Cài các thư viện cần thiết:
	```bash
	pip install -r requirements.txt
	pip install -r requirements-server.txt
	```
4. Chạy game:
	```bash
	python main.py
	```

5. (Nếu làm máy chủ) Chạy server:
	 ```bash
	 python server.py
	 ```
   
	 - Mặc định server sẽ lắng nghe trên tất cả các địa chỉ mạng (0.0.0.0) và cổng 5000.
	 - Có thể tuỳ chỉnh địa chỉ host và port:
		 ```bash
		 python server.py --host 0.0.0.0 --port 5000
		 ```
	 - Nếu muốn chia sẻ server qua Internet mà không cần mở port thủ công, có thể dùng ngrok (cần cài `pyngrok`):
		 ```bash
		 pip install pyngrok
		 python server.py --ngrok
		 ```
	 - Khi dùng `--ngrok`, server sẽ in ra địa chỉ ngrok để các máy khác kết nối.


## Chạy online (nhiều máy)

### 1. Máy chủ — chạy server
```bash
python server.py
```
Server lắng nghe trên cổng `5000`. Giữ cửa sổ này mở trong suốt ván đấu.

### 2. Tìm IP máy chủ
```bash
ipconfig
```
Lấy dòng **IPv4 Address** (ví dụ `192.168.1.5`).

### 3. Tất cả máy — chạy game
```bash
python main.py
```
- Vào **Settings** → nhập IP máy chủ vào ô **Host**, port `5000`.
- Vào **Join Online** → tạo hoặc join phòng.
- Khi đủ người, ván đấu tự bắt đầu.

---


## Chơi qua mạng khác mạng (Internet)

### 1. Máy chủ — mở port trên router
- Đăng nhập vào router/modem, tìm mục **Port Forwarding** (Chuyển tiếp cổng).
- Thêm luật chuyển tiếp cổng **5000** đến IP nội bộ của máy chủ (lấy từ `ipconfig`).
- Có thể cần tắt tường lửa hoặc cho phép cổng 5000 trên máy chủ.

### 2. Lấy IP công cộng
- Truy cập https://www.whatismyip.com/ hoặc tìm "what is my ip" trên Google để lấy địa chỉ IP công cộng.

### 3. Máy khách — nhập IP công cộng
- Khi nhập **Host** trong **Settings**, dùng IP công cộng của máy chủ, port `5000`.
- Các bước còn lại như chơi LAN.

**Lưu ý:** Chỉ nên chia sẻ IP công cộng cho người tin tưởng. Đảm bảo bảo mật cho máy chủ.

---

## Cùng mạng LAN
Dùng IP nội bộ của máy chủ (từ `ipconfig`). Không cần cấu hình thêm.



## Tạo phòng 3 người (1 người + AI)
Khi tạo phòng, chọn **3P** → chọn chế độ **Player 3** (Random / Minimax / MCTS / ML).  
Chỉ cần 2 người thật, Player 3 do server điều khiển tự động.