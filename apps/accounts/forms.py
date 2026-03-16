from django import forms
from django.contrib.auth.forms import AuthenticationForm


class PhoneAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Số điện thoại")
    password = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput)
