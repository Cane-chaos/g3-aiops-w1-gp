import re

for path in ['architecture-notebook-script.drawio', 'architecture.drawio']:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            code = f.read()

        code = code.replace(
            'Rolling z-score + Isolation Forest',
            'Rolling Z-score + EWMA + iForest'
        )
        code = code.replace(
            'Rolling Z-score + Isolation Forest',
            'Rolling Z-score + EWMA + iForest'
        )
        code = code.replace(
            '2 metric detectors',
            '3 metric detectors'
        )

        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)
            print(f"{path} updated successfully.")
    except Exception as e:
        print(f"Error reading {path}: {e}")

