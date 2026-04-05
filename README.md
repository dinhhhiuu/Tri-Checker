## Activate virtual environment:

### On macOS/Linux:
```
source venv/bin/activate
```

### On Windows:
```
venv\Scripts\activate
```

## Setting
```
pip install -r requirements.txt
```

## RUN TEST
```python
python -m tests.test
```

## RUN GAME
```python
python main.py
```

## ML: Generate data
```python
python -m src.ml.generate_data --games 50 --max-steps 200 --out data/ml_dataset.jsonl --seed 123 --p1 random --p2 random --p3 random
```

## ML: Train model
```python
python -m src.ml.train_model --data data/ml_dataset.jsonl --out-model data/models/advantage_model.joblib --include-turn
```

Chi tiết xem: `src/ml/README.md`

### Các thay đổi về MCTS và minimax algos
- Thêm thời gian tối đa để thuận toán tìm move, hiện tại là 0.3s (dòng 253, 256 trong main.py) (cho đỡ lag với nhanh hơn)
- Tăng trọng số đếm quân, thêm bonus cho cơ hội nhảy và kiểm soát trung tâm (quân ở hàn thấp hơn có giá trị hơn)
- MCTS:
    + Tăng số sim lên 2000
    + Loại bỏ việc chọn nước đi có thiên kiến (đã chọn từ 5 nước đi tốt nhất 90% thời gian), sử dụng chọn nước đi ngẫu nhiên thuần túy để khám phá tốt hơn
    + Thêm kết thúc sớm cho vị trí cuối game (≤6 quân còn lại)
- Minimax:
    + Thay thế việc xáo trộn ngẫu nhiên bằng sắp xếp dựa trên heuristic
    + Sử dụng move_score để ưu tiên nước đi hứa hẹn trước