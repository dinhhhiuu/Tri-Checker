# ML

Tài liệu này tập trung vào 2 thứ:
1) Tạo dataset bằng self-play: `src.ml.generate_data`
2) Train model baseline: `src.ml.train_model`

## 0) Chuẩn bị môi trường

### Windows (khuyến nghị dùng venv trong repo)
```powershell
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 1) Generate dataset (JSONL)

### Lệnh cơ bản
`generate_data` sẽ append vào 1 file JSONL (mỗi dòng 1 record). Nếu file đã tồn tại,
nó sẽ tự đọc dòng cuối để tiếp tục `game_id` (không bị reset về 0).

```bash
python -m src.ml.generate_data --games 50 --max-steps 200 --out data/ml_dataset.jsonl --seed 123 --p1 random --p2 random --p3 random
```

### Tham số
- `--games`: số ván self-play
- `--max-steps`: tối đa số bước (nước đi) trong 1 ván
- `--out`: đường dẫn file JSONL output
- `--seed`: seed để tái lập kết quả (đồng thời seed cho các AI dùng `random`)
- `--p1/--p2/--p3`: mode cho từng người chơi: `player | random | minimax | mcts | ml`
	- Lưu ý: trong generator không có input chuột, nên `player` sẽ được hiểu như `random`.

### Ví dụ chạy theo từng AI

Random vs Random vs Random:
```bash
python -m src.ml.generate_data --games 30 --max-steps 200 --out data/ml_random.jsonl --seed 1 --p1 random --p2 random --p3 random
```

Minimax vs Minimax vs Minimax (depth đang cố định = 2 trong code):
```bash
python -m src.ml.generate_data --games 10 --max-steps 200 --out data/ml_minimax.jsonl --seed 2 --p1 minimax --p2 minimax --p3 minimax
```

MCTS vs MCTS vs MCTS (simulations đang cố định = 100 trong code, có in log debug):
```bash
python -m src.ml.generate_data --games 10 --max-steps 200 --out data/ml_mcts.jsonl --seed 3 --p1 mcts --p2 mcts --p3 mcts
```

ML vs Random vs Random (dùng model đã train tại `data/models/advantage_model.joblib`):
```bash
python -m src.ml.generate_data --games 20 --max-steps 200 --out data/ml_ml.jsonl --seed 4 --p1 ml --p2 random --p3 random
```

### Schema mỗi dòng JSONL
Mỗi dòng là 1 object:
- `game_id`: id ván game (tự tăng)
- `step`: số bước trong ván đó (0..)
- `board`: list-of-lists (tam giác 10 hàng), giá trị ô: `0/1/2/3`
- `turn`: player đang tới lượt (1/2/3)
- `move`: đường đi đã chọn, dạng list of `[row, col]`
- `advantage_player`: nhãn “ai đang lợi thế” tại trạng thái *trước khi đi* (0 nếu hoà)
- `advantage_scores`: dict điểm heuristic cho từng player

## 2) Train model (baseline)

Model baseline dự đoán `advantage_player` từ trạng thái bàn cờ (và tuỳ chọn thêm `turn`).

Yêu cầu đã cài dependency trong `requirements.txt`:
- `numpy`, `scikit-learn`, `joblib`

Train + lưu model:
```bash
python -m src.ml.train_model --data data/ml_dataset.jsonl --out-model data/models/advantage_model.joblib --include-turn
```

Bỏ các mẫu hoà (`advantage_player==0`):
```bash
python -m src.ml.train_model --data data/ml_dataset.jsonl --drop-ties --out-model data/models/advantage_model.joblib --include-turn
```

Một số option hay dùng:
- `--class-weight balanced|none` (mặc định `balanced`)
- `--test-size 0.2` (tỉ lệ test)
- `--seed 123`

Ví dụ train nhanh hơn (test ít hơn) và tắt cân bằng lớp:
```bash
python -m src.ml.train_model --data data/ml_dataset.jsonl --out-model data/models/advantage_model.joblib --include-turn --test-size 0.1 --class-weight none
```