from datasets import load_dataset
import pandas as pd

try:
    print("Loading QDAT dataset info...")
    dataset = load_dataset("obadx/qdat", split="train", streaming=True)
    # Get first 5 rows
    rows = []
    for i, row in enumerate(dataset):
        rows.append(row)
        if i >= 4: break
    
    df = pd.DataFrame(rows)
    print("\n--- QDAT SCHEMA ---")
    print(df.columns.tolist())
    print(df.head())
    
except Exception as e:
    print(f"Error: {e}")
