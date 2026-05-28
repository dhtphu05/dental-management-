# Nhật ký Cập nhật: Tính năng Lịch biểu & Quản lý lịch hẹn qua Sidebar

## 1. Mục tiêu và Tổng quan
Chuyển đổi trải nghiệm đặt lịch hẹn (Booking) từ dạng Form chuyển trang truyền thống sang trải nghiệm mượt mà theo phong cách Single-Page Application (SPA). Lịch hẹn được render trực quan và hỗ trợ mở ngăn kéo (sidebar) lập lịch ngay góc phải mà không load lại trang. Đồng thời, luồng tạo Bệnh nhân được gom chung với luồng Lên lịch nhờ tính năng Smart Search tìm theo số điện thoại.

## 2. Chi tiết các thay đổi ở Backend (Django/Python)

* **`apps/scheduling/api_views.py`**:
  - Tạo mới `AppointmentEventsAPIView`: Cung cấp JSON data về các lịch hẹn để thư viện FullCalendar hiển thị trực quan.
  - Tạo mới `AppointmentCreateAPIView`: Endpoint dùng để hứng dữ liệu (POST) tạo lịch hẹn từ Sidebar sử dụng AJAX/Fetch API.
  - Tạo mới `PatientSearchAPIView`: Nhận parameter `phone` và trả về thông tin bệnh nhân tương ứng (Xác định bệnh nhân Cũ/Mới).

* **`apps/scheduling/forms.py`**:
  - Viết mới `SidebarAppointmentForm`: Loại bỏ input dạng chọn dropdown (ForeignKey) tẻ nhạt, mở ra hai ô nhập `phone` và `full_name`.
  - Override logic `save()`: Sử dụng `Patient.objects.get_or_create()` để động tự truy vấn bệnh nhân có sẵn hoặc tạo hoàn toàn một hồ sơ mới toanh mà không cần điều hướng sang trang "Thêm bệnh nhân".

* **`apps/scheduling/views.py` & `urls.py`**:
  - Cập nhật `AppointmentCalendarView` để truyền `SidebarAppointmentForm` xuống cho template.
  - Định tuyến (routing) đúng các endpoint API mới để fetch dữ liệu từ bên Front-end.

## 3. Chi tiết các thay đổi ở Frontend (Template & Javascript)

* **Tích hợp FullCalendar (`templates/scheduling/calendar.html`)**:
  - Gắn dependencies cho FullCalendar.js.
  - Map sự kiện click lịch và click giờ vào hàm bật Sidebar (Drawer) bên phải.

* **UI Drawer (Ngăn kéo Sidebar bên phải)**:
  - Sử dụng TailwindCSS để tạo side-panel vuốt từ phải sang trang. Chứa toàn bộ Context của `SidebarAppointmentForm`.

* **AJAX form submission**:
  - Thay vì submit làm mới trang, sử dụng Javascript Vanilla (Fetch API) để bắt sự kiện lưu: `submitAppointmentForm(event)`. Xử lý hiển thị các phản hồi thành công / lỗi tức thời.

* **Smart Search (Tự động tải & tạo bệnh nhân)**:
  - Chèn logic DOM (DOM manipulation) điền động nút tìm kiếm vào thẳng ô input Số Điện thoại.
  - Lắng nghe sự kiện `blur`, nhấn nút `Enter` hoặc nhấn thẳng nút `Tìm` trên ô số điện thoại để bắn request về `PatientSearchAPIView`.
  - Hiển thị văn bản phản hồi thông minh: xanh lá (Bệnh nhân cũ) + auto-fill trường Họ Tên; Xanh dương (Bệnh nhân mới) + tự động focus vào trường nhập tên mới; Đỏ (Lỗi kết nối hoặc Validation).