from django.core.management.base import BaseCommand

from apps.accounts.models import CustomUser, UserRole


DEFAULT_PASSWORD = "Dental@123"
DOCTORS = [
    {
        "username": "drminhanh",
        "full_name": "Nguyễn Minh Anh",
        "phone": "0909000001",
        "email": "nguyen.minh.anh@dental.local",
    },
    {
        "username": "drquanghuy",
        "full_name": "Trần Quang Huy",
        "phone": "0909000002",
        "email": "tran.quang.huy@dental.local",
    },
    {
        "username": "drthuha",
        "full_name": "Lê Thu Hà",
        "phone": "0909000003",
        "email": "le.thu.ha@dental.local",
    },
    {
        "username": "drngocbao",
        "full_name": "Phạm Ngọc Bảo",
        "phone": "0909000004",
        "email": "pham.ngoc.bao@dental.local",
    },
    {
        "username": "drthanhtam",
        "full_name": "Võ Thanh Tâm",
        "phone": "0909000005",
        "email": "vo.thanh.tam@dental.local",
    },
    {
        "username": "drhoainam",
        "full_name": "Đặng Hoài Nam",
        "phone": "0909000006",
        "email": "dang.hoai.nam@dental.local",
    },
]


class Command(BaseCommand):
    help = "Seed tài khoản bác sĩ Việt Nam cho môi trường phát triển."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Đặt lại mật khẩu mặc định cho toàn bộ bác sĩ được seed.",
        )

    def handle(self, *args, **options):
        reset_passwords = options["reset_passwords"]
        created_count = 0
        updated_count = 0

        for doctor in DOCTORS:
            user, created = CustomUser.objects.get_or_create(
                phone=doctor["phone"],
                defaults={
                    "username": doctor["username"],
                    "email": doctor["email"],
                    "first_name": doctor["full_name"],
                    "role": UserRole.DOCTOR,
                    "is_staff": True,
                    "is_active": True,
                },
            )

            user.username = doctor["username"]
            user.email = doctor["email"]
            user.first_name = doctor["full_name"]
            user.last_name = ""
            user.role = UserRole.DOCTOR
            user.is_staff = True
            user.is_active = True

            if created or reset_passwords or not user.has_usable_password():
                user.set_password(DEFAULT_PASSWORD)

            user.save()

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Tạo bác sĩ: {doctor['full_name']} | Username: {doctor['username']} | SĐT: {doctor['phone']} | Mật khẩu mặc định: {DEFAULT_PASSWORD}"
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Cập nhật bác sĩ: {doctor['full_name']} | Username: {doctor['username']} | SĐT: {doctor['phone']}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Hoàn tất seed bác sĩ. Tạo mới: {created_count}, cập nhật: {updated_count}."))
        self.stdout.write("Bác sĩ dùng username để đăng nhập; bệnh nhân mới dùng số điện thoại.")
