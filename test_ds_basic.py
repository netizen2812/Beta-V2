from datasets import load_dataset
try:
    print("Test load...")
    dataset = load_dataset("obadx/qdat", split="train", streaming=True)
    print("Iterate...")
    for row in dataset:
        print(f"ID: {row['id']}")
        break
except Exception as e:
    import traceback
    traceback.print_exc()
