from django import forms
from django.utils import timezone
from app.models import Appointment, SpecialtyChoices


class AppointmentRequestForm(forms.ModelForm):
    requested_date = forms.DateTimeField(
        label='Preferred appointment date and time',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Select date and time...',
                'style': 'width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-family: inherit; font-size: 14px; background: #ffffff; cursor: pointer;',
            }
        ),
        input_formats=['%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %I:%M %p']
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
        # Set minimum selectable date to current time
        now_str = timezone.now().strftime('%Y-%m-%dT%H:%M')
        self.fields['requested_date'].widget.attrs['min'] = now_str

