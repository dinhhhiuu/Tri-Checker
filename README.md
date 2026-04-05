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