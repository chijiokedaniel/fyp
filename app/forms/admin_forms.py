from django import forms
from django.contrib.auth import get_user_model
from app.models import DoctorProfile, SpecialtyChoices, UserRole

User = get_user_model()


class AdminDoctorCreationForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={
            'placeholder': 'Dr. John',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Last Name",
        widget=forms.TextInput(attrs={
            'placeholder': 'Smith',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'placeholder': 'doctor.smith@hospital.com',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    phone = forms.CharField(
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'placeholder': '+1 (555) 000-0000',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    specialty = forms.ChoiceField(
        choices=SpecialtyChoices.choices,
        required=True,
        label="Medical Specialty",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    bio = forms.CharField(
        required=False,
        label="Professional Bio",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Board-certified specialist with 10+ years of experience...',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    password = forms.CharField(
        required=True,
        label="Initial Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    auto_approve = forms.BooleanField(
        required=False,
        initial=True,
        label="Approve Doctor Profile Immediately",
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone', ''),
            role=UserRole.DOCTOR
        )
        profile = DoctorProfile.objects.create(
            user=user,
            specialty=data['specialty'],
            bio=data.get('bio', ''),
            approved=data.get('auto_approve', True)
        )
        return user, profile


class AdminPatientCreationForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={
            'placeholder': 'Jane',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Last Name",
        widget=forms.TextInput(attrs={
            'placeholder': 'Doe',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    email = forms.EmailField(
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'placeholder': 'jane.doe@example.com',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    phone = forms.CharField(
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'placeholder': '+1 (555) 000-0000',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    address = forms.CharField(
        required=False,
        label="Home Address",
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': '124 Healthcare Way, Suite 100...',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )
    password = forms.CharField(
        required=True,
        label="Initial Password",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            role=UserRole.PATIENT
        )
        return user
