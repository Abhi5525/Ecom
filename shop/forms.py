from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class SignUpForm(UserCreationForm):
    username  = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'label': "Username",
            'class': 'form-control',
            'placeholder': 'Username'
        }))
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'label':"Email",
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    password1 = forms.CharField(

        label="Password",
        widget=forms.PasswordInput(attrs={
            'label': "Password",
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'label': "Confirm Password",
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'label': "Email",
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'label': "Password",
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )
