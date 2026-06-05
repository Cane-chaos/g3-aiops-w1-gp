import re

path = 'SUBMIT.md'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'chạy hai detector thật sự có trong hệ thống: Rolling Z-score và Isolation Forest',
    'chạy ba detector thật sự có trong hệ thống: Rolling Z-score, EWMA và Isolation Forest'
)

code = code.replace(
    '1 giờ gần nhất, còn Isolation Forest',
    '1 giờ gần nhất, EWMA phản ứng nhanh với thay đổi xu hướng, còn Isolation Forest'
)

code = code.replace(
    '2. Ít nhất 2 detector: Rolling Z-score và Isolation Forest',
    '2. Ít nhất 3 detector: Rolling Z-score, EWMA và Isolation Forest'
)

code = code.replace(
    'Ít nhất 2 detector: Rolling Z-score và Isolation Forest',
    'Ít nhất 3 detector: Rolling Z-score, EWMA và Isolation Forest'
)

code = code.replace(
    'không có EWMA, IQR, MAD, Drain3 template mining hoặc Isolation Forest model artifact `.joblib`',
    'không có IQR, MAD, Drain3 template mining hoặc Isolation Forest model artifact `.joblib`'
)

code = code.replace(
    'Không được ghi EWMA, IQR, MAD, Drain3',
    'Không được ghi IQR, MAD, Drain3'
)

code = code.replace(
    'hai detector này bổ sung nhau',
    'ba detector này bổ sung nhau'
)

code = code.replace(
    'Rolling Z-score như detector thống kê dễ giải thích và Isolation Forest như detector xác nhận đa biến.',
    'Rolling Z-score và EWMA như các detector thống kê bổ trợ lẫn nhau để phát hiện spike và trend shift, cùng với Isolation Forest như detector xác nhận đa biến.'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("SUBMIT.md updated successfully.")
