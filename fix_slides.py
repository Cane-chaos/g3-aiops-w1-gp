import re

with open('docs/g3-lab-presentation.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove Deliverables and Closing slides
# Using regex to remove the <section class="slide"> that contains "Deliverables"
html = re.sub(r'<section class="slide">\s*<div class="wrap">\s*<div class="eyebrow">Deliverables.*?</section>', '', html, flags=re.DOTALL)
# Remove the <section class="slide"> that contains "Thông điệp chính"
html = re.sub(r'<section class="slide">\s*<div class="title-wrap">\s*<div class="eyebrow">Closing.*?</section>', '', html, flags=re.DOTALL)


# 2. Update Detector Comparison Slide
html = html.replace(
    '<div class="evidence-strip">\n        <div class="evidence-pill"><b>21</b><span>Z-score points</span></div>\n        <div class="evidence-pill"><b>226</b><span>IF points</span></div>\n        <div class="evidence-pill"><b>18:24</b><span>first IF anomaly</span></div>\n        <div class="evidence-pill"><b>20:00</b><span>Z-score peak window</span></div>\n      </div>',
    '<div class="evidence-strip">\n        <div class="evidence-pill"><b>21</b><span>Z-score points</span></div>\n        <div class="evidence-pill"><b>44</b><span>EWMA points</span></div>\n        <div class="evidence-pill"><b>226</b><span>IF points</span></div>\n        <div class="evidence-pill"><b>18:24</b><span>first IF anomaly</span></div>\n      </div>'
)

evidence_notes_old = """      <div class="evidence-notes">
        <div class="evidence-note">
          <h3>Z-score bắt gì?</h3>
          <p>Bắt biến động memory mạnh. Vì chỉ đơn biến, nó không phải detector đầu tiên cho degradation đa biến.</p>
        </div>
        <div class="evidence-note">
          <h3>Isolation Forest bắt gì?</h3>
          <p>Bắt trạng thái xấu đồng thời: memory 56.59%, GC 161.1ms, p99 406.5ms lúc 18:24.</p>
        </div>
        <div class="evidence-note">
          <h3>Ảnh này đọc thế nào?</h3>
          <p>Nền xám là memory %, vòng xanh là Z-score, chấm đỏ là IF. OOM line cho thấy collapse sau degradation.</p>
        </div>
      </div>"""

evidence_notes_new = """      <div class="evidence-notes" style="grid-template-columns: repeat(4, 1fr);">
        <div class="evidence-note">
          <h3>Z-score bắt gì?</h3>
          <p>Bắt đột biến memory so với trung bình 1 giờ tĩnh. Thích hợp tìm spike/drop.</p>
        </div>
        <div class="evidence-note">
          <h3>EWMA bắt gì?</h3>
          <p>Bắt sự dịch chuyển xu hướng (drift) nhờ trọng số nghiêng về quá khứ gần, nhạy hơn Z-score tiêu chuẩn.</p>
        </div>
        <div class="evidence-note">
          <h3>Isolation Forest bắt gì?</h3>
          <p>Bắt trạng thái xấu đa biến: memory 56.59%, GC 161.1ms, p99 406.5ms lúc 18:24.</p>
        </div>
        <div class="evidence-note">
          <h3>Ảnh này đọc thế nào?</h3>
          <p>Nền xám là memory %, 🔵 vòng xanh là Z-score, 🔺 tam giác xanh lá là EWMA, 🔴 chấm đỏ là IF.</p>
        </div>
      </div>"""
html = html.replace(evidence_notes_old, evidence_notes_new)


# 3. Update Evidence Map Slide
evidence_map_old = """          <tr>
            <td>Incident Z-score spike</td>
            <td><code>anomalies.csv</code></td>
            <td>Rolling Z-score <code>|z| &gt; 3</code></td>
            <td><code>19:33:30</code>: memory about 1509 MB; <code>20:00</code>: restart drop.</td>
          </tr>"""
evidence_map_new = """          <tr>
            <td>Incident Z-score spike</td>
            <td><code>anomalies.csv</code></td>
            <td>Rolling Z-score <code>|z| &gt; 3</code></td>
            <td><code>19:33:30</code>: memory about 1509 MB; <code>20:00</code>: restart drop.</td>
          </tr>
          <tr>
            <td>EWMA drift detection</td>
            <td><code>anomalies.csv</code></td>
            <td>EWMA <code>|score| &gt; 3</code></td>
            <td>Phát hiện xu hướng tăng dần của memory sớm hơn và đặc hơn so với Z-score.</td>
          </tr>"""
html = html.replace(evidence_map_old, evidence_map_new)

with open('docs/g3-lab-presentation.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("g3-lab-presentation.html updated successfully.")
