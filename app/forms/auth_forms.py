from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

from app.models import UserRole

User = get_user_model()


class PatientRegistrationForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'placeholder': 'patient@example.com',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )

    class Meta:
        model = User
        fields = ['email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.role = UserRole.PATIENT
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class DoctorApplicationForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'placeholder': 'doctor@example.com',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )

    class Meta:
        model = User
        fields = ['email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.role = UserRole.DOCTOR
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'placeholder': 'your.email@example.com',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )
    password = forms.CharField(
        required=True,
        label="Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )
