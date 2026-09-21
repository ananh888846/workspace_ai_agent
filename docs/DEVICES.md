# Devices V2

## Mục tiêu

Quản lý ESP32, ESP32-CAM, Luckfox, Home Assistant và thiết bị tương lai như các identity độc lập.

## Model

```text
User
 └── Device
      ├── capabilities
      └── observations/events
```

Device không phải User.

## ESP32-CAM

Hỗ trợ về kiến trúc:

- image.capture
- face.verify
- event.detect
- sensor.read
- voice/command gateway khi phù hợp

## 10 camera trở lên

Thiết kế không giới hạn cố định 10 camera. Mỗi camera có device_uuid, capability, status và last_seen. Có thể mở rộng qua gateway/message bus ở phase scale.

## Identity flow

```text
Device
 ↓
Observation
 ↓
Verification / Detection
 ↓
User reference nếu policy cho phép
 ↓
Event
```

## Security

Device credential và user identity phải tách nhau. Device không được tự quyết định quyền đọc data package.


## Organization / Resource binding V2.1

Device có thể thuộc một Organization và gắn với Resource cụ thể:

`Organization → Resource → Device → Observation → Event`

Binding này giúp xác định camera/cảm biến thuộc phòng nào, khu vực nào hoặc workspace nào. Device vẫn là identity độc lập và không kế thừa quyền User tự động.
