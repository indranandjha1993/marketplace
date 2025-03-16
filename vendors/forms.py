from django import forms
from django.core.exceptions import ValidationError
from .models import Vendor, VendorBankAccount, VendorDocument


class VendorAccountForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['tax_id', 'commission_rate']
        widgets = {
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Tax ID'}),
            'commission_rate': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter Commission Rate'}),
        }


class VendorBankAccountForm(forms.ModelForm):
    class Meta:
        model = VendorBankAccount
        fields = ['account_name', 'account_number', 'bank_name', 'branch_name', 'ifsc_code', 'swift_code']
        widgets = {
            'account_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Account Name'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Account Number'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Bank Name'}),
            'branch_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Branch Name'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter IFSC Code'}),
            'swift_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter SWIFT Code'}),
        }


class VendorDocumentForm(forms.Form):
    DOCUMENT_TYPE_CHOICES = VendorDocument.DOCUMENT_TYPE_CHOICES
    ALLOWED_FILE_TYPES = ['pdf', 'jpg', 'jpeg', 'png']

    def __init__(self, *args, **kwargs):
        exclude_types = kwargs.pop('exclude_types', [])
        super().__init__(*args, **kwargs)

        available_choices = [(k, v) for k, v in self.DOCUMENT_TYPE_CHOICES if k not in exclude_types]
        self.fields['document_type'].choices = available_choices

    document_type = forms.ChoiceField(
        choices=DOCUMENT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    document = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'required': True,
            'name': 'document'
        }),
        required=True,
        error_messages={
            'required': 'Please select a file to upload.'
        }
    )

    def clean_document(self):
        document = self.cleaned_data.get('document')
        if not document:
            raise ValidationError("Please select a file to upload.")
        if not any(document.name.lower().endswith(ext) for ext in self.ALLOWED_FILE_TYPES):
            raise ValidationError(f"Unsupported file type. Allowed types are {', '.join(self.ALLOWED_FILE_TYPES)}.")
        if document.size > 10 * 1024 * 1024:  # 10MB limit
            raise ValidationError("File size must not exceed 10MB.")
        return document
