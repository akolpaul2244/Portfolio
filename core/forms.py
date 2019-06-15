"""
Contact form with input sanitization.
"""
import bleach
from django import forms
from .models import ContactMessage


ALLOWED_TAGS = []   # No HTML allowed in contact form


class ContactForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your full name',
            'class': 'form-input',
            'autocomplete': 'name',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'you@example.com',
            'class': 'form-input',
            'autocomplete': 'email',
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'What is this about?',
            'class': 'form-input',
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Tell me about your project, opportunity, or question…',
            'class': 'form-textarea',
            'rows': 6,
        })
    )

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']

    def clean_name(self):
        return bleach.clean(self.cleaned_data['name'], tags=ALLOWED_TAGS, strip=True)

    def clean_subject(self):
        return bleach.clean(self.cleaned_data['subject'], tags=ALLOWED_TAGS, strip=True)

    def clean_message(self):
        return bleach.clean(self.cleaned_data['message'], tags=ALLOWED_TAGS, strip=True)