# Dental Project

He thong quan ly phong kham nha khoa duoc xay dung bang Django 6 theo kien truc module, gom cac phan he quan ly nguoi dung, benh nhan, lich hen, dieu tri rang va hoa don.

## Tinh nang chinh

- Custom User model voi role: `Admin`, `Doctor`, `Receptionist`, `Patient`
- CRUD day du cho:
  - Benh nhan
  - Lich hen
  - Dich vu
  - Hoa don
- Booking page da nang cap:
  - Multi-step booking flow
  - Time slots disable theo lich da dat
  - Mobile-first grid cho khung gio
- Doctor dashboard:
  - Collapsible sidebar
  - Stats cards
  - Bang lich hen hien dai
  - Line chart bang Chart.js
- Odontogram cho bac si:
  - 32 rang chia 4 cung ham
  - Modal cap nhat tinh trang rang
  - Color coding cho tinh trang rang
- Tu dong hoa nghiep vu:
  - Chan trung lich bac si
  - Tu dong tao odontogram cho benh nhan moi
  - Tu dong cap nhat trang thai rang khi hoan tat lieu trinh
  - Tu dong sinh va tinh tong hoa don tu treatment plan
- Design System dung Tailwind CSS + Lucide Icons

## Cau truc du an

```text
.
├── core/                 # Django settings, urls, wsgi, asgi
├── apps/
│   ├── accounts/         # User, role, dashboard
│   ├── patients/         # Ho so benh nhan
│   ├── scheduling/       # Lich hen va booking flow
│   ├── clinical/         # Odontogram, treatment plan, services
│   └── billing/          # Hoa don
├── templates/            # Giao dien HTML
├── static/               # Tai nguyen static
├── manage.py
└── README.md
```

## Cong nghe

- Python 3.14
- Django 6.0.3
- SQLite
- Tailwind CSS Browser CDN
- Chart.js
- Lucide Icons

## Cai dat va chay local

### 1. Tao virtualenv

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Cai dependency

```bash
pip install "Django>=6,<6.1"
```

### 3. Chay migrate

```bash
python manage.py migrate
```

### 4. Tao tai khoan admin

```bash
python manage.py createsuperuser
```

### 5. Chay server

```bash
python manage.py runserver
```

Truy cap:

- Dashboard: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Chay test

```bash
python manage.py test
```

## Business Logic quan trong

### Appointment validation

- Mot bac si khong the co 2 lich hen trung ngay va gio
- Kiem tra duoc thuc hien o model `Appointment`

### Odontogram automation

- Khi tao benh nhan moi, he thong tu dong tao 32 rang mac dinh
- Khi treatment plan hoan tat, trang thai rang lien quan duoc cap nhat

### Invoice automation

- Hoa don duoc tao tu dong theo treatment plan
- Tong tien duoc tinh tu cac service da chon

## Giao dien noi bat

- Doctor dashboard voi sidebar thu gon
- Booking page multi-step co thanh tien trinh
- Odontogram tuong tac voi modal cap nhat tinh trang rang
- CRUD pages dong nhat theo design system xanh nha khoa

## Git workflow goi y

```bash
git init
git add .
git commit -m "Initial commit"
```

Neu muon lam viec theo nhanh rieng:

```bash
git checkout -b codex/setup-project
```

## Luu y

- File `db.sqlite3` da duoc dua vao `.gitignore`
- Thu muc `.venv/` va cac file cache Python cung da duoc bo qua
- Project hien dang toi uu cho phat trien local
