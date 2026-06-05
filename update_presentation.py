import re

path = 'docs/g3-lab-presentation.html'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    '<h2>Hai detector: Rolling Z-score và Isolation Forest</h2>',
    '<h2>Ba detector: Rolling Z-score, EWMA và Isolation Forest</h2>'
)

code = code.replace(
    '<p>Nhóm sử dụng hai detector',
    '<p>Nhóm sử dụng ba detector'
)

code = code.replace(
    '<td>abs(z) &gt; 3</td>',
    '<td>abs(z) &gt; 3</td>\n          </tr>\n          <tr>\n            <td><strong>EWMA</strong></td>\n            <td>Memory drift</td>\n            <td>span=120, abs(score) &gt; 3</td>'
)

code = code.replace(
    '<span>Z-score + Isolation Forest</span>',
    '<span>Z-score + EWMA + Isolation Forest</span>'
)

code = code.replace(
    'Chạy lại 2 detector metric',
    'Chạy lại 3 detector metric'
)

code = code.replace(
    'và 2 detector có anomaly points',
    'và 3 detector có anomaly points'
)

code = code.replace(
    'So sánh Rolling Z-score và Isolation Forest.',
    'So sánh Z-score, EWMA và Isolation Forest.'
)

code = code.replace(
    'có code chạy lại, 2 detector,',
    'có code chạy lại, 3 detector,'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("g3-lab-presentation.html updated successfully.")
