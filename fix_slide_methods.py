import re

with open('docs/g3-lab-presentation.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Fix 1: Slide 01 2 detectors -> 3 detectors
html = html.replace('<b>2 detectors</b><span>Z-score + EWMA + Isolation Forest</span>', '<b>3 detectors</b><span>Z-score + EWMA + Isolation Forest</span>')

# Fix 2: Slide 04 Method Table
method_old = """      <h2>Detector set: chỉ dùng 2 phương pháp</h2>
      <table style="margin-top:24px">
        <thead>
          <tr><th>Detector</th><th>Vai trò</th><th>Rule / Features</th><th>Points</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Rolling Z-score</strong></td>
            <td>Detector thống kê đơn biến, dễ giải thích</td>
            <td><code>abs(memory_mb_rolling_zscore) &gt; 3</code></td>
            <td><strong>21</strong></td>
          </tr>
          <tr>
            <td><strong>Isolation Forest</strong></td>
            <td>Detector đa biến cho trạng thái bất thường tổng hợp</td>
            <td><code>memory_pct</code>, GC, latency, 5xx, restarts</td>
            <td><strong>226</strong></td>
          </tr>
        </tbody>
      </table>"""

method_new = """      <h2>Detector set: triển khai 3 phương pháp</h2>
      <table style="margin-top:24px; font-size: 0.9em;">
        <thead>
          <tr><th>Detector</th><th>Vai trò</th><th>Rule / Features</th><th>Points</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Rolling Z-score</strong></td>
            <td>Detector thống kê đơn biến, dễ giải thích</td>
            <td><code>abs(zscore) &gt; 3</code></td>
            <td><strong>21</strong></td>
          </tr>
          <tr>
            <td><strong>EWMA</strong></td>
            <td>Phát hiện xu hướng (trend shift) và memory drift</td>
            <td><code>abs(ewma_score) &gt; 3</code>, span=120</td>
            <td><strong>44</strong></td>
          </tr>
          <tr>
            <td><strong>Isolation Forest</strong></td>
            <td>Detector đa biến cho trạng thái bất thường tổng hợp</td>
            <td><code>memory_pct</code>, GC, latency, 5xx, restarts</td>
            <td><strong>226</strong></td>
          </tr>
        </tbody>
      </table>"""
html = html.replace(method_old, method_new)

# Fix 3: "Câu cần nói"
html = html.replace('Câu cần nói: <strong>06:30 không phải IF hay Z-score bắt.</strong> 06:30', '<strong>Lưu ý quan trọng:</strong> 06:30 không phải do IF, EWMA hay Z-score bắt. 06:30')

with open('docs/g3-lab-presentation.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("g3-lab-presentation.html method slides fixed successfully.")
