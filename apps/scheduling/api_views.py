from django.http import JsonResponse
from django.views.generic import View
from apps.scheduling.models import Appointment
from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole

class AppointmentEventsAPIView(RoleRequiredMixin, View):
    allowed_roles = (UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR)

    def get(self, request, *args, **kwargs):
        queryset = Appointment.objects.select_related("patient", "doctor")
        
        # Doctor role only sees their own appointments
        if request.user.role == UserRole.DOCTOR:
            queryset = queryset.filter(doctor=request.user)
        else:
            doctor_id = request.GET.get("doctor_id")
            if doctor_id:
                queryset = queryset.filter(doctor_id=doctor_id)
                
        events = []
        for appt in queryset:
            # Create a localized datetime combining date and time_slot
            start_dt = f"{appt.date.isoformat()}T{appt.time_slot.strftime('%H:%M:%S')}"
            
            # If we know the treatment duration, we could add end time, currently let's just do start time
            # Or add a default 30 min duration
            
            DOCTOR_COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f97316", "#eab308", "#14b8a6", "#06b6d4", "#6366f1", "#10b981", "#ef4444"]
            bg_color = DOCTOR_COLORS[appt.doctor.id % len(DOCTOR_COLORS)]

            
            events.append({
                "id": str(appt.pk),
                "title": f"[{appt.get_status_display()}] {appt.patient.full_name}",
                "start": start_dt,
                "backgroundColor": bg_color,
                "borderColor": bg_color,
                "textColor": "#ffffff",
                "extendedProps": {
                    "patient_name": appt.patient.full_name,
                    "doctor_name": appt.doctor.get_full_name() or appt.doctor.username,
                    "status": appt.get_status_display(),
                    "reason": appt.reason,
                    "url": f"/scheduling/{appt.pk}/"
                }
            })
            
        return JsonResponse(events, safe=False)

import json
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from apps.scheduling.forms import AppointmentForm, SidebarAppointmentForm

@method_decorator(csrf_exempt, name='dispatch')
class AppointmentCreateAPIView(RoleRequiredMixin, View):
    allowed_roles = (UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.DOCTOR)
    
    def post(self, request, *args, **kwargs):
        try:
            # We assume form data is sent as application/x-www-form-urlencoded
            form = SidebarAppointmentForm(request.POST)
            if form.is_valid():
                appt = form.save()
                return JsonResponse({"status": "success", "id": appt.pk})
            else:
                return JsonResponse({"status": "error", "errors": form.errors}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


from apps.patients.models import Patient

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
