from django import forms
from .models import *

class LoginForm(forms.Form):
    msisdn = forms.CharField(
        max_length=15,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control ',
                'placeholder': 'Phone number'
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
