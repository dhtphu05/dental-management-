from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from apps.clinical.models import Tooth
from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import UserRole
import json

class ToothUpdateAPIView(RoleRequiredMixin, View):
    allowed_roles = (UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)

    def post(self, request, pk):
        tooth = get_object_or_404(Tooth, pk=pk)
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"error": "Invalid payload"}, status=400)
            
        status = data.get("status")
        notes = data.get("notes")
        
        if status:
            tooth.status = status
        if notes is not None:
            tooth.notes = notes
            
        tooth.last_updated_by = request.user
        tooth.save()
        
        return JsonResponse({
            "id": tooth.pk,
            "status": tooth.status,
            "notes": tooth.notes,
            "updated_at": tooth.updated_at.strftime("%H:%M %d/%m/%Y"),
            "doctor": request.user.full_name or request.user.get_full_name() or request.user.username
        })
