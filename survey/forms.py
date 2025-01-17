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

class QuestionnaireDataForm(forms.Form):
    ccc_number = forms.CharField(label="CCC Number",max_length=15)
    mfl_code = forms.CharField(label="MFL Code",max_length=15)
