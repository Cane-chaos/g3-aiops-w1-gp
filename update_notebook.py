import json

path = 'notebooks/analysis.ipynb'
with open(path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

for cell in notebook.get('cells', []):
    if cell['cell_type'] == 'markdown':
        new_source = []
        for line in cell['source']:
            line = line.replace('hai detector', 'ba detector')
            line = line.replace('two detector', 'three detector')
            line = line.replace('2 detector', '3 detector')
            line = line.replace('Z-score is the explainable univariate memory detector. Isolation Forest is multivariate', 'Z-score and EWMA are the explainable univariate memory detectors. Isolation Forest is multivariate')
            new_source.append(line)
        cell['source'] = new_source
    elif cell['cell_type'] == 'code':
        new_source = []
        for line in cell['source']:
            line = line.replace("anomaly_rows = anomalies[anomalies[['z_anomaly', 'if_anomaly']].any(axis=1)]", "anomaly_rows = anomalies[anomalies[['z_anomaly', 'ewma_anomaly', 'if_anomaly']].any(axis=1)]")
            line = line.replace("'z_anomaly', 'if_anomaly'", "'z_anomaly', 'ewma_anomaly', 'if_anomaly'")
            new_source.append(line)
        cell['source'] = new_source

with open(path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1)

print("notebooks/analysis.ipynb updated successfully.")
