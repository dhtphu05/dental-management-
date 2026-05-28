import re

with open("apps/scheduling/api_views.py", "r") as f:
    text = f.read()

new_api = """from apps.patients.models import Patient

class PatientSearchAPIView(RoleRequiredMixin, View):
    allowed_roles = (UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR)
    
    def get(self, request, *args, **kwargs):
        phone = request.GET.get('phone', '').strip()
        if not phone:
            return JsonResponse({"status": "error", "message": "Vui lòng cung cấp số điện thoại"}, status=400)
            
        try:
            patient = Patient.objects.get(phone=phone)
            return JsonResponse({
                "status": "success", 
                "data": {
                    "full_name": patient.full_name,
                    "phone": patient.phone,
                    "id": patient.pk
                }
            })
        except Patient.DoesNotExist:
            return JsonResponse({"status": "not_found", "message": "Bệnh nhân chưa tồn tại trong hệ thống. Hãy nhập tên để tạo mới."}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
"""

if "PatientSearchAPIView" not in text:
    text = text + "\n\n" + new_api

# Also update the forms import in api_views
text = text.replace("from apps.scheduling.forms import AppointmentForm", "from apps.scheduling.forms import AppointmentForm, SidebarAppointmentForm")

# Update create endpoint to use Sidebar form
text = text.replace("form = AppointmentForm(request.POST)", "form = SidebarAppointmentForm(request.POST)")

with open("apps/scheduling/api_views.py", "w") as f:
    f.write(text)
