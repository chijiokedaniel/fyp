from django import forms
from django.utils import timezone
from app.models import Appointment, DoctorWorkingHours, SpecialtyChoices, DayOfWeek


class AppointmentRequestForm(forms.ModelForm):
    requested_date = forms.DateField(
        label='Preferred appointment date',
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'placeholder': 'Select date...',
                'style': 'width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-family: inherit; font-size: 14px; background: #ffffff; cursor: pointer;',
            }
        ),
        input_formats=['%Y-%m-%d']
    )

    class Meta:
        model = Appointment
        fields = ['requested_date', 'specialty', 'reason', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'specialty': 'Problem specialty',
            'reason': 'Primary concern',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['specialty'].choices = SpecialtyChoices.choices
        # Set minimum selectable date to today
        today_str = timezone.now().strftime('%Y-%m-%d')
        self.fields['requested_date'].widget.attrs['min'] = today_str

    def clean_requested_date(self):
        date_val = self.cleaned_data.get('requested_date')
        if date_val and date_val < timezone.now().date():
            raise forms.ValidationError("You cannot select a date in the past.")
        return date_val

    def save(self, commit=True):
        instance = super().save(commit=False)
        date_val = self.cleaned_data.get('requested_date')
        if date_val:
            # Convert date to datetime at midnight (00:00:00)
            naive_dt = timezone.datetime.combine(date_val, timezone.datetime.min.time())
            instance.requested_date = timezone.make_aware(naive_dt) if timezone.is_naive(naive_dt) else naive_dt
        if commit:
            instance.save()
        return instance


class DoctorWorkingHoursForm(forms.ModelForm):
    class Meta:
        model = DoctorWorkingHours
        fields = ['day', 'start_time', 'end_time', 'is_available']
        widgets = {
            'day': forms.HiddenInput(),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'style': 'padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px;'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'style': 'padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px;'}),
            'is_available': forms.CheckboxInput(attrs={'style': 'width: 18px; height: 18px; cursor: pointer;'}),
        }


class AppointmentAcceptForm(forms.Form):
    confirmed_date = forms.DateTimeField(
        label="Confirmed Date & Time",
        widget=forms.TextInput(attrs={
            'placeholder': 'Select confirmed date and time...',
            'style': 'width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-family: inherit; font-size: 14px; background: #ffffff;',
        }),
        input_formats=['%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %I:%M %p']
    )


class AppointmentRejectForm(forms.Form):
    rejection_reason = forms.CharField(
        label="Reason for Rejection",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Please type the reason for rejecting this appointment...',
            'style': 'width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-family: inherit; font-size: 14px;',
        }),
        required=True
    )
