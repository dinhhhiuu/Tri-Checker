# Tri-Checker — Network Guide

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

## Cùng mạng LAN
Dùng IP nội bộ của máy chủ (từ `ipconfig`). Không cần cấu hình thêm.



## Tạo phòng 3 người (1 người + AI)
Khi tạo phòng, chọn **3P** → chọn chế độ **Player 3** (Random / Minimax / MCTS / ML).  
Chỉ cần 2 người thật, Player 3 do server điều khiển tự động.