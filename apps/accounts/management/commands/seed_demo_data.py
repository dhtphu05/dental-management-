from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand

from apps.accounts.models import CustomUser, UserRole
from apps.billing.models import Invoice, InvoiceStatus
from apps.clinical.models import Service, Tooth, ToothStatus, TreatmentPlan, TreatmentPlanStatus
from apps.patients.models import Patient
from apps.patients.signals import TOOTH_NUMBERS
from apps.scheduling.models import Appointment, AppointmentStatus


DEFAULT_PASSWORD = "Dental@123"

STAFF_USERS = [
    {
        "username": "admin",
        "phone": "0909000000",
        "full_name": "Lê Quản Trị",
        "role": UserRole.ADMIN,
        "email": "admin@dental.local",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "username": "letan01",
        "phone": "0909111111",
        "full_name": "Phạm Thu Ngân",
        "role": UserRole.RECEPTIONIST,
        "email": "reception@dental.local",
        "is_staff": True,
        "is_superuser": False,
    },
]

DOCTORS = [
    ("drminhanh", "0909000001", "Nguyễn Minh Anh", "nguyen.minh.anh@dental.local"),
    ("drquanghuy", "0909000002", "Trần Quang Huy", "tran.quang.huy@dental.local"),
    ("drthuha", "0909000003", "Lê Thu Hà", "le.thu.ha@dental.local"),
    ("drngocbao", "0909000004", "Phạm Ngọc Bảo", "pham.ngoc.bao@dental.local"),
    ("drthanhtam", "0909000005", "Võ Thanh Tâm", "vo.thanh.tam@dental.local"),
    ("drhoainam", "0909000006", "Đặng Hoài Nam", "dang.hoai.nam@dental.local"),
]

PATIENTS = [
    {
        "phone": "0912000001",
        "full_name": "Nguyễn Thị Mai",
        "email": "nguyen.thi.mai@demo.local",
        "date_of_birth": date(1997, 4, 12),
        "address": "Quận 3, TP. Hồ Chí Minh",
        "medical_history": "Dị ứng nhẹ với thuốc tê lidocaine.",
        "notes": "Ưu tiên khám buổi sáng.",
        "create_account": True,
    },
    {
        "phone": "0912000002",
        "full_name": "Trần Quốc Bảo",
        "email": "tran.quoc.bao@demo.local",
        "date_of_birth": date(1992, 8, 20),
        "address": "Quận Bình Thạnh, TP. Hồ Chí Minh",
        "medical_history": "Có tiền sử viêm nướu.",
        "notes": "Từng điều trị tủy răng 26.",
        "create_account": True,
    },
    {
        "phone": "0912000003",
        "full_name": "Phạm Gia Hân",
        "email": "pham.gia.han@demo.local",
        "date_of_birth": date(2001, 1, 3),
        "address": "Thành phố Thủ Đức, TP. Hồ Chí Minh",
        "medical_history": "Không có bệnh lý nền.",
        "notes": "Quan tâm niềng răng thẩm mỹ.",
        "create_account": False,
    },
    {
        "phone": "0912000004",
        "full_name": "Lê Hoàng Nam",
        "email": "le.hoang.nam@demo.local",
        "date_of_birth": date(1988, 11, 15),
        "address": "Quận 7, TP. Hồ Chí Minh",
        "medical_history": "Tăng huyết áp đã kiểm soát.",
        "notes": "Nên xác nhận lịch trước 1 ngày.",
        "create_account": False,
    },
    {
        "phone": "0912000005",
        "full_name": "Võ Thanh Trúc",
        "email": "vo.thanh.truc@demo.local",
        "date_of_birth": date(1995, 6, 29),
        "address": "Quận 10, TP. Hồ Chí Minh",
        "medical_history": "Đã bọc sứ răng cửa hàm trên.",
        "notes": "Muốn tư vấn thêm về tẩy trắng răng.",
        "create_account": True,
    },
]

SERVICES = [
    ("Khám tổng quát", Decimal("150000"), timedelta(minutes=30), "Khám và tư vấn tình trạng răng miệng tổng quát."),
    ("Cạo vôi răng", Decimal("400000"), timedelta(minutes=45), "Làm sạch mảng bám và đánh bóng răng."),
    ("Trám răng thẩm mỹ", Decimal("550000"), timedelta(minutes=45), "Điều trị sâu răng và phục hồi mô răng."),
    ("Nhổ răng khôn", Decimal("1800000"), timedelta(minutes=90), "Tiểu phẫu nhổ răng khôn có gây tê."),
    ("Điều trị tủy", Decimal("2200000"), timedelta(minutes=90), "Điều trị tủy răng viêm hoặc hoại tử."),
    ("Tẩy trắng răng", Decimal("1200000"), timedelta(minutes=60), "Tẩy trắng bằng ánh sáng lạnh."),
]


class Command(BaseCommand):
    help = "Seed dữ liệu demo đầy đủ cho giao diện phòng khám nha khoa."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Đặt lại mật khẩu mặc định cho các tài khoản demo.",
        )

    def handle(self, *args, **options):
        self.reset_passwords = options["reset_passwords"]
        self.password_hash = make_password(DEFAULT_PASSWORD)

        staff = self.seed_staff_users()
        doctors = self.seed_doctors()
        patients = self.seed_patients()
        services = self.seed_services()
        self.seed_appointments_and_clinical_data(doctors, patients, services)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Đã seed xong dữ liệu demo đầy đủ."))
        self.stdout.write("Bệnh nhân dùng số điện thoại để đăng nhập; nhân sự nội bộ dùng username.")
        self.stdout.write(f"Mật khẩu mặc định: {DEFAULT_PASSWORD}")
        self.stdout.write(f"Quản trị viên: username `{staff['admin'].username}`")
        self.stdout.write(f"Lễ tân: username `{staff['receptionist'].username}`")
        self.stdout.write("Bác sĩ: drminhanh, drquanghuy, drthuha, drngocbao, drthanhtam, drhoainam")

    def upsert_user(self, *, username, phone, full_name, role, email, is_staff=False, is_superuser=False):
        user, created = CustomUser.objects.get_or_create(
            phone=phone,
            defaults={
                "username": username,
                "email": email,
                "first_name": full_name,
                "role": role,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
                "password": self.password_hash,
            },
        )
        user.username = username
        user.email = email
        user.first_name = full_name
        user.last_name = ""
        user.role = role
        user.is_staff = is_staff or role == UserRole.ADMIN
        user.is_superuser = is_superuser
        user.is_active = True
        if created or self.reset_passwords or not user.has_usable_password():
            user.password = self.password_hash
        user.save()
        return user

    def seed_staff_users(self):
        result = {}
        for payload in STAFF_USERS:
            user = self.upsert_user(**payload)
            key = "admin" if payload["role"] == UserRole.ADMIN else "receptionist"
            result[key] = user
        return result

    def seed_doctors(self):
        doctors = []
        for username, phone, full_name, email in DOCTORS:
            doctors.append(
                self.upsert_user(
                    username=username,
                    phone=phone,
                    full_name=full_name,
                    role=UserRole.DOCTOR,
                    email=email,
                    is_staff=True,
                    is_superuser=False,
                )
            )
        return doctors

    def ensure_patient_teeth(self, patient):
        existing_numbers = set(patient.teeth.values_list("tooth_number", flat=True))
        missing = [
            Tooth(patient=patient, tooth_number=number)
            for number in TOOTH_NUMBERS
            if number not in existing_numbers
        ]
        if missing:
            Tooth.objects.bulk_create(missing)

    def seed_patients(self):
        patients = []
        for payload in PATIENTS:
            patient, _ = Patient.objects.update_or_create(
                phone=payload["phone"],
                defaults={
                    "full_name": payload["full_name"],
                    "email": payload["email"],
                    "date_of_birth": payload["date_of_birth"],
                    "address": payload["address"],
                    "medical_history": payload["medical_history"],
                    "notes": payload["notes"],
                },
            )
            self.ensure_patient_teeth(patient)
            if payload["create_account"]:
                user = self.upsert_user(
                    username=payload["phone"],
                    phone=payload["phone"],
                    full_name=payload["full_name"],
                    role=UserRole.PATIENT,
                    email=payload["email"],
                    is_staff=False,
                    is_superuser=False,
                )
                if patient.user_id != user.id:
                    patient.user = user
                    patient.save(update_fields=["user"])
            patients.append(patient)
        return patients

    def seed_services(self):
        services = {}
        for name, price, duration, description in SERVICES:
            service, _ = Service.objects.update_or_create(
                name=name,
                defaults={
                    "price": price,
                    "estimated_duration": duration,
                    "description": description,
                },
            )
            services[name] = service
        return services

    def upsert_appointment(self, *, patient, doctor, appointment_date, slot, status, reason, notes):
        appointment, _ = Appointment.objects.update_or_create(
            patient=patient,
            doctor=doctor,
            date=appointment_date,
            time_slot=slot,
            defaults={
                "status": status,
                "reason": reason,
                "notes": notes,
            },
        )
        return appointment

    def upsert_plan(self, *, appointment, diagnosis, notes, status, resulting_status, tooth_numbers, service_names, services):
        plan, _ = TreatmentPlan.objects.get_or_create(
            appointment=appointment,
            defaults={
                "diagnosis": diagnosis,
                "notes": notes,
                "status": status,
                "resulting_tooth_status": resulting_status,
            },
        )
        plan.diagnosis = diagnosis
        plan.notes = notes
        plan.status = status
        plan.resulting_tooth_status = resulting_status
        plan.save()

        teeth = Tooth.objects.filter(
            patient=appointment.patient,
            tooth_number__in=tooth_numbers,
        )
        plan.teeth.set(teeth)
        plan.services.set([services[name] for name in service_names])

        if status == TreatmentPlanStatus.COMPLETED:
            plan.save()

        return plan

    def seed_appointments_and_clinical_data(self, doctors, patients, services):
        today = date.today()

        appointments = [
            {
                "patient": patients[0],
                "doctor": doctors[0],
                "date": today - timedelta(days=3),
                "slot": time(8, 0),
                "status": AppointmentStatus.COMPLETED,
                "reason": "Đau răng hàm trên bên phải",
                "notes": "Đã chụp phim và tư vấn điều trị.",
                "plan": {
                    "diagnosis": "Sâu răng 16, cần trám phục hồi.",
                    "notes": "Đã xử lý sạch mô sâu và trám composite.",
                    "status": TreatmentPlanStatus.COMPLETED,
                    "resulting_status": ToothStatus.TREATED,
                    "tooth_numbers": [16],
                    "service_names": ["Khám tổng quát", "Trám răng thẩm mỹ"],
                    "invoice_status": InvoiceStatus.PAID,
                },
            },
            {
                "patient": patients[0],
                "doctor": doctors[2],
                "date": today - timedelta(days=12),
                "slot": time(14, 30),
                "status": AppointmentStatus.COMPLETED,
                "reason": "Cạo vôi và kiểm tra nướu",
                "notes": "Đã nhắc bệnh nhân tái khám sau 6 tháng.",
                "plan": {
                    "diagnosis": "Viêm nướu nhẹ, nhiều mảng bám vùng răng cửa dưới.",
                    "notes": "Đã cạo vôi, đánh bóng và hướng dẫn vệ sinh răng miệng.",
                    "status": TreatmentPlanStatus.COMPLETED,
                    "resulting_status": ToothStatus.NORMAL,
                    "tooth_numbers": [31, 32, 41, 42],
                    "service_names": ["Khám tổng quát", "Cạo vôi răng"],
                    "invoice_status": InvoiceStatus.PAID,
                },
            },
            {
                "patient": patients[0],
                "doctor": doctors[4],
                "date": today - timedelta(days=28),
                "slot": time(8, 30),
                "status": AppointmentStatus.COMPLETED,
                "reason": "Tẩy trắng răng thẩm mỹ",
                "notes": "Bệnh nhân mong muốn tăng tông màu răng trước sự kiện.",
                "plan": {
                    "diagnosis": "Men răng ổn định, phù hợp tẩy trắng thẩm mỹ.",
                    "notes": "Đã thực hiện tẩy trắng ánh sáng lạnh, dặn tránh thực phẩm sẫm màu 48 giờ.",
                    "status": TreatmentPlanStatus.COMPLETED,
                    "resulting_status": ToothStatus.NORMAL,
                    "tooth_numbers": [11, 12, 21, 22],
                    "service_names": ["Khám tổng quát", "Tẩy trắng răng"],
                    "invoice_status": InvoiceStatus.ISSUED,
                },
            },
            {
                "patient": patients[0],
                "doctor": doctors[1],
                "date": today - timedelta(days=47),
                "slot": time(10, 0),
                "status": AppointmentStatus.COMPLETED,
                "reason": "Khám tổng quát sau sinh",
                "notes": "Kiểm tra ê buốt nhẹ vùng cổ răng.",
                "plan": {
                    "diagnosis": "Mòn cổ răng nhẹ vùng 13 và 14, chưa cần can thiệp phục hồi.",
                    "notes": "Tư vấn dùng kem giảm ê buốt và theo dõi sau 3 tháng.",
                    "status": TreatmentPlanStatus.COMPLETED,
                    "resulting_status": ToothStatus.NORMAL,
                    "tooth_numbers": [13, 14],
                    "service_names": ["Khám tổng quát"],
                    "invoice_status": InvoiceStatus.PAID,
                },
            },
            {
                "patient": patients[0],
                "doctor": doctors[3],
                "date": today - timedelta(days=61),
                "slot": time(15, 30),
                "status": AppointmentStatus.COMPLETED,
                "reason": "Khám kiểm tra sau cạo vôi",
                "notes": "Không phát hiện thêm chỉ định điều trị.",
                "plan": None,
            },
            {
                "patient": patients[1],
                "doctor": doctors[1],
                "date": today - timedelta(days=1),
                "slot": time(9, 30),
                "status": AppointmentStatus.COMPLETED,
                "reason": "Ê buốt kéo dài ở răng 26",
                "notes": "Đã xác nhận viêm tủy.",
                "plan": {
                    "diagnosis": "Viêm tủy răng 26, chỉ định điều trị tủy.",
                    "notes": "Đã hoàn tất điều trị tủy và tái tạo xoang trám.",
                    "status": TreatmentPlanStatus.COMPLETED,
                    "resulting_status": ToothStatus.TREATED,
                    "tooth_numbers": [26],
                    "service_names": ["Khám tổng quát", "Điều trị tủy"],
                    "invoice_status": InvoiceStatus.ISSUED,
                },
            },
            {
                "patient": patients[1],
                "doctor": doctors[5],
                "date": today - timedelta(days=18),
                "slot": time(13, 0),
                "status": AppointmentStatus.COMPLETED,
                "reason": "Đau vùng răng khôn hàm dưới",
                "notes": "Đã chụp phim và xử lý trong cùng buổi.",
                "plan": {
                    "diagnosis": "Răng khôn 48 mọc lệch gây viêm lợi trùm.",
                    "notes": "Đã nhổ răng khôn 48, kê đơn giảm đau và dặn tái khám.",
                    "status": TreatmentPlanStatus.COMPLETED,
                    "resulting_status": ToothStatus.MISSING,
                    "tooth_numbers": [48],
                    "service_names": ["Khám tổng quát", "Nhổ răng khôn"],
                    "invoice_status": InvoiceStatus.PAID,
                },
            },
            {
                "patient": patients[1],
                "doctor": doctors[3],
                "date": today - timedelta(days=35),
                "slot": time(10, 30),
                "status": AppointmentStatus.COMPLETED,
                "reason": "Kiểm tra răng sứ và ê buốt",
                "notes": "Bệnh nhân từng điều trị phục hình ở nơi khác.",
                "plan": {
                    "diagnosis": "Răng 24 có phục hình sứ cũ, viền nướu kích ứng nhẹ.",
                    "notes": "Đã vệ sinh, đánh giá khớp cắn và hẹn theo dõi thêm.",
                    "status": TreatmentPlanStatus.COMPLETED,
                    "resulting_status": ToothStatus.CROWN,
                    "tooth_numbers": [24],
                    "service_names": ["Khám tổng quát"],
                    "invoice_status": InvoiceStatus.ISSUED,
                },
            },
            {
                "patient": patients[1],
                "doctor": doctors[0],
                "date": today - timedelta(days=52),
                "slot": time(8, 30),
                "status": AppointmentStatus.COMPLETED,
                "reason": "Cạo vôi định kỳ và kiểm tra viêm nướu",
                "notes": "Bệnh nhân đáp ứng tốt sau điều trị trước.",
                "plan": {
                    "diagnosis": "Viêm nướu khu trú vùng răng hàm dưới, nhiều cao răng bám mặt trong.",
                    "notes": "Đã cạo vôi, đánh bóng và tái hướng dẫn vệ sinh kẽ răng.",
                    "status": TreatmentPlanStatus.COMPLETED,
                    "resulting_status": ToothStatus.NORMAL,
                    "tooth_numbers": [36, 37, 46, 47],
                    "service_names": ["Khám tổng quát", "Cạo vôi răng"],
                    "invoice_status": InvoiceStatus.PAID,
                },
            },
            {
                "patient": patients[1],
                "doctor": doctors[2],
                "date": today - timedelta(days=73),
                "slot": time(14, 0),
                "status": AppointmentStatus.COMPLETED,
                "reason": "Tái khám sau điều trị tủy",
                "notes": "Không còn ê buốt, theo dõi tốt.",
                "plan": None,
            },
            {
                "patient": patients[4],
                "doctor": doctors[0],
                "date": today - timedelta(days=9),
                "slot": time(9, 0),
                "status": AppointmentStatus.COMPLETED,
                "reason": "Trám răng cửa bị mẻ",
                "notes": "Bệnh nhân quan tâm yếu tố thẩm mỹ.",
                "plan": {
                    "diagnosis": "Mẻ cạnh cắn răng 11, chỉ định trám thẩm mỹ.",
                    "notes": "Đã trám composite, chỉnh khớp cắn nhẹ.",
                    "status": TreatmentPlanStatus.COMPLETED,
                    "resulting_status": ToothStatus.TREATED,
                    "tooth_numbers": [11],
                    "service_names": ["Khám tổng quát", "Trám răng thẩm mỹ"],
                    "invoice_status": InvoiceStatus.PAID,
                },
            },
            {
                "patient": patients[4],
                "doctor": doctors[5],
                "date": today - timedelta(days=22),
                "slot": time(13, 30),
                "status": AppointmentStatus.COMPLETED,
                "reason": "Khám nướu chảy máu khi chải răng",
                "notes": "Bệnh nhân muốn cải thiện thẩm mỹ và sức khỏe nướu.",
                "plan": {
                    "diagnosis": "Viêm nướu nhẹ lan tỏa, mảng bám vùng răng trước.",
                    "notes": "Đã làm sạch, hướng dẫn dùng chỉ nha khoa và hẹn tái khám.",
                    "status": TreatmentPlanStatus.COMPLETED,
                    "resulting_status": ToothStatus.NORMAL,
                    "tooth_numbers": [11, 12, 21, 22, 31, 41],
                    "service_names": ["Khám tổng quát", "Cạo vôi răng"],
                    "invoice_status": InvoiceStatus.ISSUED,
                },
            },
            {
                "patient": patients[4],
                "doctor": doctors[2],
                "date": today - timedelta(days=44),
                "slot": time(10, 30),
                "status": AppointmentStatus.COMPLETED,
                "reason": "Tư vấn thẩm mỹ răng cửa",
                "notes": "Chưa thực hiện điều trị, chỉ đánh giá ban đầu.",
                "plan": None,
            },
            {
                "patient": patients[2],
                "doctor": doctors[2],
                "date": today,
                "slot": time(10, 0),
                "status": AppointmentStatus.CONFIRMED,
                "reason": "Tư vấn niềng răng và lấy dấu",
                "notes": "Khách muốn tư vấn thêm chi phí theo từng giai đoạn.",
                "plan": {
                    "diagnosis": "Sai khớp cắn nhẹ, đang trong giai đoạn tư vấn.",
                    "notes": "Chưa bắt đầu điều trị chính thức.",
                    "status": TreatmentPlanStatus.PLANNED,
                    "resulting_status": ToothStatus.NORMAL,
                    "tooth_numbers": [11, 21],
                    "service_names": ["Khám tổng quát"],
                    "invoice_status": InvoiceStatus.DRAFT,
                },
            },
            {
                "patient": patients[3],
                "doctor": doctors[0],
                "date": today,
                "slot": time(14, 0),
                "status": AppointmentStatus.PENDING,
                "reason": "Đặt lịch cạo vôi răng",
                "notes": "Khách mới đặt qua form công khai.",
                "plan": None,
            },
            {
                "patient": patients[4],
                "doctor": doctors[3],
                "date": today + timedelta(days=1),
                "slot": time(8, 30),
                "status": AppointmentStatus.CONFIRMED,
                "reason": "Tẩy trắng răng",
                "notes": "Đã tư vấn chống ê buốt sau tẩy trắng.",
                "plan": None,
            },
            {
                "patient": patients[0],
                "doctor": doctors[4],
                "date": today + timedelta(days=2),
                "slot": time(15, 0),
                "status": AppointmentStatus.CANCELLED,
                "reason": "Tái khám sau trám",
                "notes": "Bệnh nhân xin dời lịch sang tuần sau.",
                "plan": None,
            },
            {
                "patient": patients[1],
                "doctor": doctors[5],
                "date": today + timedelta(days=3),
                "slot": time(13, 30),
                "status": AppointmentStatus.CONFIRMED,
                "reason": "Nhổ răng khôn hàm dưới",
                "notes": "Cần ký cam kết trước thủ thuật.",
                "plan": {
                    "diagnosis": "Răng khôn 48 mọc lệch, chỉ định tiểu phẫu.",
                    "notes": "Đã lên kế hoạch nhổ răng khôn vào buổi hẹn tới.",
                    "status": TreatmentPlanStatus.IN_PROGRESS,
                    "resulting_status": ToothStatus.MISSING,
                    "tooth_numbers": [48],
                    "service_names": ["Khám tổng quát", "Nhổ răng khôn"],
                    "invoice_status": InvoiceStatus.DRAFT,
                },
            },
            {
                "patient": patients[3],
                "doctor": doctors[2],
                "date": today + timedelta(days=4),
                "slot": time(10, 30),
                "status": AppointmentStatus.CONFIRMED,
                "reason": "Khám và cạo vôi định kỳ",
                "notes": "Đã nhắn khách đến sớm 10 phút.",
                "plan": None,
            },
        ]

        for item in appointments:
            appointment = self.upsert_appointment(
                patient=item["patient"],
                doctor=item["doctor"],
                appointment_date=item["date"],
                slot=item["slot"],
                status=item["status"],
                reason=item["reason"],
                notes=item["notes"],
            )
            plan_payload = item["plan"]
            if not plan_payload:
                continue

            plan = self.upsert_plan(
                appointment=appointment,
                diagnosis=plan_payload["diagnosis"],
                notes=plan_payload["notes"],
                status=plan_payload["status"],
                resulting_status=plan_payload["resulting_status"],
                tooth_numbers=plan_payload["tooth_numbers"],
                service_names=plan_payload["service_names"],
                services=services,
            )
            invoice = Invoice.objects.get(treatment_plan=plan)
            if invoice.status != plan_payload["invoice_status"]:
                invoice.status = plan_payload["invoice_status"]
                invoice.save(update_fields=["status", "updated_at"])
