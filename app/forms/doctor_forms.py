from datetime import datetime, timedelta

from django import forms
from django.utils import timezone
from app.models import Appointment, DoctorWorkingHours, SpecialtyChoices, DayOfWeek
from app.utils.appointment_slots import is_slot_available, get_working_window


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
    requested_time = forms.TimeField(
        label='Preferred appointment time',
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Appointment
        fields = ['requested_date', 'specialty', 'reason', 'notes']
        widgets = {
            'specialty': forms.Select(attrs={
                'style': 'width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-family: inherit; font-size: 14px; background: #ffffff;'
            }),
            'reason': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe your primary health concern or reason for visit...',
                'style': 'width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-family: inherit; font-size: 14px; min-height: 90px; resize: vertical;'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Additional notes for the doctor (optional)...',
                'style': 'width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-family: inherit; font-size: 14px; min-height: 100px; resize: vertical;'
            }),
        }
        labels = {
            'specialty': 'Problem specialty',
            'reason': 'Primary concern',
        }

    def __init__(self, *args, doctor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['specialty'].choices = SpecialtyChoices.choices
        self.doctor = doctor

        if doctor and hasattr(doctor, 'doctor_profile') and doctor.doctor_profile:
            self.fields['specialty'].initial = doctor.doctor_profile.specialty
            self.fields['specialty'].disabled = True
            self.fields['specialty'].widget.attrs['style'] = (
                'width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; '
                'font-family: inherit; font-size: 14px; background: #f1f5f9; color: #64748b; cursor: not-allowed;'
            )
            doc_name = doctor.get_full_name() or doctor.email
            self.fields['specialty'].help_text = f"Locked to Dr. {doc_name}'s specialty."

        # Set minimum selectable date to today
        today_str = timezone.now().strftime('%Y-%m-%d')
        self.fields['requested_date'].widget.attrs['min'] = today_str

    def clean_requested_date(self):
        date_val = self.cleaned_data.get('requested_date')
        if date_val and date_val < timezone.now().date():
            raise forms.ValidationError("You cannot select a date in the past.")
        return date_val

    def clean(self):
        cleaned_data = super().clean()
        requested_date = cleaned_data.get('requested_date')
        requested_time = cleaned_data.get('requested_time')

        if not requested_date or not requested_time:
            return cleaned_data

        requested_dt = timezone.make_aware(datetime.combine(requested_date, requested_time))
        if requested_dt < timezone.now():
            raise forms.ValidationError('Please choose a future appointment slot.')

        if self.doctor:
            working_window = get_working_window(self.doctor, requested_date)
            if not working_window:
                raise forms.ValidationError('The selected date is outside this doctor’s working hours.')

            start_time, end_time = working_window
            slot_start = timezone.make_aware(datetime.combine(requested_date, start_time))
            slot_end = timezone.make_aware(datetime.combine(requested_date, end_time))
            if requested_dt < slot_start or requested_dt + timedelta(minutes=30) > slot_end:
                raise forms.ValidationError('The selected time is outside this doctor’s working hours.')

            if not is_slot_available(self.doctor, requested_dt):
                raise forms.ValidationError('That time slot has already been booked. Please choose another available slot.')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        date_val = self.cleaned_data.get('requested_date')
        time_val = self.cleaned_data.get('requested_time')
        if date_val and time_val:
            requested_dt = timezone.make_aware(datetime.combine(date_val, time_val))
            instance.requested_date = requested_dt
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
