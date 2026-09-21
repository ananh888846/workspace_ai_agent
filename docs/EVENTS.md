# Events / Activities V2

## Phân biệt

Observation là dữ liệu quan sát thô hoặc kết quả từ device/provider.

Event là sự kiện có ý nghĩa hệ thống.

Activity là hoạt động đã được tổng hợp/ghi nhận theo domain.

```text
Observation → Event → Activity
```

## Ví dụ về nhà

```text
ESP32-CAM
 ↓
face detected
 ↓
face verification
 ↓
event: home_arrival
 ↓
activity: arrived_home
```

## Ví dụ thuốc

```text
Prescription image
 ↓
Vision extraction
 ↓
Medication schedule
 ↓
Reminder event/action
```

Không coi inference của AI là fact tuyệt đối. Confidence, source và status phải được lưu để audit.

## Event processing

Phase đầu dùng application service. Sau này có thể thêm queue/event bus nếu throughput tăng.


## Activity Session V2.1

Khi cần đo một phiên sử dụng, dùng Activity Session để giữ session_type, started_at, ended_at, duration_seconds, user/resource/organization, status và confidence.

Ví dụ bathroom:

`person_detected → door_open → entered → inside → door_open → exited → Activity Session`

Duration-based classification chỉ là inference có detection_method, không phải medical fact.

## Task đối soát

Task/Work Order biểu diễn công việc được giao; Activity Session/Activity biểu diễn những gì hệ thống ghi nhận. Hai nguồn được so sánh bởi Anomaly Detection Agent để tìm mismatch, không tự kết luận fraud.
