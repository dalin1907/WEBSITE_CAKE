from django import forms
from .models import SupplierRequest, SupplierProfile


class SupplierRequestForm(forms.ModelForm):
    class Meta:
        model = SupplierRequest
        fields = ['ingredient', 'requested_quantity', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }


class SupplierClaimForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label='Ghi chú/offer')


class SupplierProfileForm(forms.ModelForm):
    class Meta:
        model = SupplierProfile
        fields = ['company_name', 'contact_email', 'phone', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }