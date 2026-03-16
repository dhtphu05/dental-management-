from django import forms
from django.contrib.auth.forms import AuthenticationForm


class MixedAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Tên đăng nhập / Số điện thoại")
    password = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput)

    error_messages = {
        "invalid_login": "Tên đăng nhập, số điện thoại hoặc mật khẩu không đúng.",
        "inactive": "Tài khoản này đã bị vô hiệu hóa.",
    }
