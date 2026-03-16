from django.contrib.auth.backends import ModelBackend

from apps.accounts.models import CustomUser, UserRole


class UsernameOrPatientPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get(CustomUser.USERNAME_FIELD)
        if not identifier or not password:
            return None

        user = (
            CustomUser.objects.filter(username=identifier).first()
            or CustomUser.objects.filter(phone=identifier, role=UserRole.PATIENT).first()
        )

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
