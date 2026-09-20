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
