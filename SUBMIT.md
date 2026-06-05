# SUBMIT.md

## 1. Phản ánh của nhóm

Trong bài lab này, nhóm xây dựng một pipeline AIOps có thể chạy lại từ raw telemetry để điều tra incident của ShopX. Dữ liệu đầu vào gồm các file metric CSV của nhiều service và log JSONL của `cart-service` / `order-service`. Nhóm dùng notebook để thuyết minh, xem biểu đồ và trình bày evidence, còn logic tính toán nằm trong `scripts/` để đảm bảo kết quả có thể reproduce bằng `make analyze`.

Nhóm chọn hướng điều tra **metric-first, log-backtrace**. Đầu tiên pipeline đọc metric của `cart-service`, build feature như `memory_mb`, `memory_pct`, GC pause, p99 latency, 5xx rate và restart count. Sau đó pipeline chạy ba detector thật sự có trong hệ thống: Rolling Z-score, EWMA và Isolation Forest. Rolling Z-score giúp phát hiện memory spike/drop so với baseline 1 giờ gần nhất, EWMA phản ứng nhanh với thay đổi xu hướng, còn Isolation Forest giúp bắt trạng thái bất thường đa biến giữa memory, GC, latency, 5xx và restart.

Sau khi metric detector xác định `cart-service` là service chính và chỉ ra degradation window, nhóm mới dùng log để backtrace nguyên nhân. Log analysis hiện tại không dùng Drain3; pipeline dùng fixed pattern extraction trên JSONL để trích các pattern như `ProductCatalogCache eviction failed`, `GC overhead limit warning`, `Container OOMKilled` và `OutOfMemoryError imminent`. Vì vậy `06:30:08` được ghi là supporting log evidence sớm nhất sau khi backtrace, không phải anomaly do Z-score hay Isolation Forest phát hiện.

Kết quả cuối cùng cho thấy metric giúp trả lời WHEN và WHERE ở tầng hệ thống, còn log giúp giải thích WHAT ở tầng cơ chế lỗi. Cách ghép hai nguồn evidence theo timestamp giúp nhóm đưa ra giả thuyết root cause: `cart-service` gặp memory pressure liên quan `ProductCatalogCache`, dẫn tới GC pause tăng, latency xấu đi, OOMKilled và restart loop.

---

## 2. Những điều nhóm học được

- Không nên kết luận root cause chỉ từ một metric hoặc một dòng log.
- Metric detector nên được dùng để chọn service và time window trước khi đọc log sâu.
- Rolling Z-score dễ giải thích, phù hợp để bắt spike/drop mạnh của memory.
- Isolation Forest bắt được trạng thái bất thường đa biến nhưng khó giải thích hơn detector thống kê.
- Log pattern extraction giúp biến raw JSONL thành evidence có timestamp, line number, pod và message rõ ràng.
- `06:30` là supporting log evidence sau khi backtrace, không phải kết quả trực tiếp của IF/Z-score.
- Không được ghi IQR, MAD, Drain3 hoặc model artifact nếu hệ thống hiện tại chưa implement chúng.
- Không tính precision, recall hoặc F1 vì dataset không có ground-truth label rõ ràng.

---

## 3. Đánh đổi giữa các detector

Rolling Z-score có ưu điểm là nhanh, dễ triển khai và dễ giải thích cho đội vận hành. Khi detector báo anomaly, nhóm có thể chỉ rõ memory lệch bao nhiêu sigma so với baseline gần nhất. Trong bài này, Rolling Z-score bắt được 21 anomaly points và hữu ích nhất quanh giai đoạn memory spike/drop gần OOM/restart.

Isolation Forest phân tích nhiều feature cùng lúc nên phù hợp hơn với trạng thái degradation tổng hợp. Trong bài này, Isolation Forest dùng `memory_pct`, `jvm_gc_pause_ms_avg`, `http_p99_latency_ms`, `http_5xx_rate` và `container_restart_count`; detector bắt được 226 anomaly points và lần đầu flag degradation lúc `2026-06-01T18:24:00+00:00`. Đổi lại, Isolation Forest phụ thuộc vào feature engineering và contamination, nên cần bảng evidence để giải thích vì sao một điểm bị xem là bất thường.

Phương án thực tế của nhóm là dùng Rolling Z-score và EWMA như các detector thống kê bổ trợ lẫn nhau để phát hiện spike và trend shift, cùng với Isolation Forest như detector xác nhận đa biến. Hai detector này bổ sung nhau, không thay thế log analysis.

---

## 4. Metric và log khác nhau như thế nào?

Metric trả lời:

```text
WHEN  — metric bắt đầu bất thường lúc nào?
WHERE — service và metric nào xấu trước?
```

Log trả lời:

```text
WHAT — lỗi cụ thể nào xảy ra?
WHY  — cơ chế nào có thể gây ra lỗi?
```

Trong incident này, metric cho thấy `cart-service` có memory, GC pause, p99 latency, 5xx và restart xấu đi. Log bổ sung evidence về heap pressure, cache eviction failure, OOMKilled và OOM imminent. Hai nguồn dữ liệu được nối với nhau theo timestamp để hình thành timeline RCA.

---

## 5. Kết luận kỹ thuật

Giả thuyết có độ tin cậy cao nhất là `cart-service` gặp memory pressure tăng dần, có thể liên quan đến memory leak hoặc cache eviction thất bại trong `ProductCatalogCache`. Quá trình này dẫn tới GC pause tăng, p99 latency xấu đi, xuất hiện OOMKilled, restart lặp và làm hệ thống mất ổn định. Metric detector xác định degradation chính, còn log-backtrace cho thấy supporting evidence sớm hơn tại `06:30:08`.

---

## 6. Phân công công việc cho 10 thành viên

| Thành viên | Vai trò / Phụ trách chính | Sản phẩm bàn giao |
|---|---|---|
| Bùi Vũ Quang Vinh | PM — Điều phối nhóm, thống nhất scope và checklist nộp bài | Kế hoạch nhóm, checklist, review cuối |
| Phạm Hữu Tiến Thành | PM2 — Tổng hợp báo cáo và chuẩn hóa nội dung tiếng Việt | `FINDINGS.md`, `SUBMIT.md`, tài liệu nhóm |
| Nguyễn Hữu Định | Tech Lead — Thiết kế pipeline metric-first, log-backtrace và chốt RCA | Kiến trúc pipeline, kết luận kỹ thuật, slide |
| Hoàng Nhật Thành | Data validation — Kiểm tra metric CSV, timestamp, schema và data gap | `validation_summary.json`, ghi chú data quality |
| Nguyễn Hưng Thịnh | Cart-service EDA — Phân tích memory, GC, latency, 5xx và restart | `cart_metrics_evidence.png`, metric summary |
| Trần Mạnh Trường | Cross-service EDA — Kiểm tra order/payment/api-gateway để nhận diện impact | ghi chú downstream impact và metric liên quan |
| Lê Kim Dũng | Statistical detector — Implement và giải thích Rolling Z-score | `anomalies.csv`, Z-score evidence |
| Nguyễn Ngọc Giao | Feature engineering — Build feature memory ratio, rate và rolling statistics | `features_cart_service.csv` |
| Nguyễn Công Thịnh | ML detector — Implement Isolation Forest và detector comparison | `detector_comparison.csv`, IF evidence |
| Phan Đức Tài | Log analysis — Parse JSONL và extract fixed log patterns | `log_pattern_events.csv`, `log_pattern_counts.csv` |

### Cơ chế phối hợp

- PM và PM2 chịu trách nhiệm điều phối, tổng hợp và kiểm tra deliverables.
- Tech Lead chịu trách nhiệm quyết định technical narrative và đảm bảo không ghi phương pháp chưa implement.
- Nhóm metric chịu trách nhiệm data validation, feature engineering, detector và biểu đồ.
- Nhóm log chịu trách nhiệm JSONL parsing, pattern extraction và log-backtrace evidence.
- Cả nhóm review lại `FINDINGS.md`, `SUBMIT.md` và slide trước khi nộp.

---

## 7. Danh sách sản phẩm cần nộp

```text
[x] Code chạy được end-to-end bằng make analyze
[x] Ít nhất 3 detector: Rolling Z-score, EWMA và Isolation Forest
[x] Biểu đồ metric evidence
[x] Biểu đồ anomaly detector comparison
[x] Log pattern extraction từ JSONL
[x] Log pattern count time series
[x] Correlation timeline
[x] FINDINGS.md tiếng Việt
[x] SUBMIT.md tiếng Việt
[x] HTML slide cho thuyết trình nhóm
```

Ghi chú: hệ thống hiện tại không có IQR, MAD, Drain3 template mining hoặc Isolation Forest model artifact `.joblib`, nên các mục đó không được liệt kê là sản phẩm đã làm.
