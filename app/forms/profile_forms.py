from django import forms
from django.contrib.auth import get_user_model

from app.models import DoctorProfile, SpecialtyChoices

User = get_user_model()


class PatientProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150, required=True, label="First Name",
        widget=forms.TextInput(attrs={'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 14px;'})
    )
    last_name = forms.CharField(
        max_length=150, required=True, label="Last Name",
        widget=forms.TextInput(attrs={'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 14px;'})
    )
    email = forms.EmailField(
        required=True, label="Email Address",
        widget=forms.EmailInput(attrs={'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 14px;'})
    )
    phone = forms.CharField(
        max_length=24, required=False, label="Phone Number",
        widget=forms.TextInput(attrs={'placeholder': '+1 (555) 000-0000', 'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 14px;'})
    )
    address = forms.CharField(
        required=False, label="Home Address / Details",
        widget=forms.Textarea(attrs={'rows': 3, 'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 14px;'})
    )
    profile_picture = forms.ImageField(
        required=False, label="Profile Picture",
        widget=forms.FileInput(attrs={'accept': 'image/*', 'id': 'id_profile_picture', 'style': 'width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'profile_picture']


class PatientOnboardingForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. John',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Last Name",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Doe',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )
    phone = forms.CharField(
        max_length=24,
        required=True,
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'placeholder': '+1 (555) 000-0000',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )
    address = forms.CharField(
        required=False,
        label="Home Address / Contact Details",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Street address, city, postal code...',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'address']


class DoctorProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150, required=True, label="First Name",
        widget=forms.TextInput(attrs={'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 14px;'})
    )
    last_name = forms.CharField(
        max_length=150, required=True, label="Last Name",
        widget=forms.TextInput(attrs={'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 14px;'})
    )
    email = forms.EmailField(
        required=True, label="Email Address",
        widget=forms.EmailInput(attrs={'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 14px;'})
    )
    specialty = forms.ChoiceField(
        choices=SpecialtyChoices.choices, required=True, label="Medical Specialty",
        widget=forms.Select(attrs={'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 14px;'})
    )
    bio = forms.CharField(
        required=False, label="Medical Bio",
        widget=forms.Textarea(attrs={'rows': 3, 'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 14px;'})
    )
    profile_picture = forms.ImageField(
        required=False, label="Profile Picture",
        widget=forms.FileInput(attrs={'accept': 'image/*', 'id': 'id_profile_picture', 'style': 'width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'})
    )

    class Meta:
        model = DoctorProfile
        fields = ['specialty', 'bio', 'profile_picture']

    def save(self, user=None, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
        if user:
            user.email = self.cleaned_data.get('email', user.email)
            user.first_name = self.cleaned_data.get('first_name', user.first_name)
            user.last_name = self.cleaned_data.get('last_name', user.last_name)
            user.save()
        return profile


class DoctorOnboardingForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Sarah',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Last Name",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Jenkins',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )
    phone = forms.CharField(
        max_length=24,
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'placeholder': '+1 (555) 000-0000',
            'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'
        })
    )
    specialty = forms.ChoiceField(
        choices=SpecialtyChoices.choices,
        required=True,
        label="Medical Specialty",
        widget=forms.Select(attrs={'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'})
    )
    bio = forms.CharField(
        required=False,
        label="Professional Medical Biography",
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe your medical background, qualifications, and areas of expertise...', 'style': 'width: 100%; padding: 12px 14px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'})
    )
    profile_picture = forms.ImageField(
        required=False,
        label="Profile Picture (Optional)",
        widget=forms.FileInput(attrs={'accept': 'image/*', 'style': 'width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 10px; background: #f8fafc; font-family: inherit; font-size: 14px;'})
    )

    class Meta:
        model = DoctorProfile
        fields = ['specialty', 'bio', 'profile_picture']

    def save(self, user=None, commit=True):
        profile = super().save(commit=False)
        if user:
            profile.user = user
            user.first_name = self.cleaned_data.get('first_name', user.first_name)
            user.last_name = self.cleaned_data.get('last_name', user.last_name)
            user.phone = self.cleaned_data.get('phone', user.phone)
            user.save()
        if commit:
            profile.save()
        return profile
