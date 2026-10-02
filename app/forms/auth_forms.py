from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

from app.models import UserRole

User = get_user_model()


class RegistrationForm(forms.ModelForm):
    ROLE_CHOICES = [
        (UserRole.PATIENT, 'Patient'),
        (UserRole.DOCTOR, 'Doctor'),
    ]

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial=UserRole.PATIENT,
        label="Account Type",
        widget=forms.RadioSelect(attrs={
            'class': 'role-radio-input',
        })
    )
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'placeholder': 'your.email@example.com',
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
        fields = ['email', 'role']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role not in [UserRole.PATIENT, UserRole.DOCTOR]:
            raise forms.ValidationError("Please select a valid account role (Patient or Doctor).")
        return role

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        user.username = email
        user.email = email
        user.role = self.cleaned_data['role']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class PatientRegistrationForm(RegistrationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = UserRole.PATIENT
        self.fields['role'].widget = forms.HiddenInput()

    def clean_role(self):
        return UserRole.PATIENT


class DoctorApplicationForm(RegistrationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = UserRole.DOCTOR
        self.fields['role'].widget = forms.HiddenInput()

    def clean_role(self):
        return UserRole.DOCTOR


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
