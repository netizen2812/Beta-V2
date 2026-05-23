from datasets import load_dataset, Audio
import pandas as pd

try:
    print("Loading QDAT dataset info (no decode)...")
    dataset = load_dataset("obadx/qdat", split="train", streaming=True)
    dataset = dataset.cast_column("audio", Audio(decode=False))
    
    # Get first 5 rows
    rows = []
    for i, row in enumerate(dataset):
        # Remove the actual audio bytes for printing
        row_copy = row.copy()
        row_copy['audio'] = f"<{len(row['audio']['bytes'])} bytes>"
        rows.append(row_copy)
        if i >= 4: break
    
    df = pd.DataFrame(rows)
    print("\n--- QDAT SCHEMA ---")
    print(df.head())
    
except Exception as e:
    print(f"Error: {e}")
