from django import forms
from .models import SupplierProposal, Delivery, SupplierProfile, OrderRequest


class SupplierProfileForm(forms.ModelForm):
    class Meta:
        model = SupplierProfile
        fields = ["company_name", "contact_name", "contact_email", "phone", "address"]


class OrderRequestForm(forms.ModelForm):
    class Meta:
        model = OrderRequest
        fields = ["ingredient", "quantity", "note"]
        widgets = {
            "ingredient": forms.HiddenInput(),
        }



class AdminOrderRequestForm(forms.ModelForm):
    class Meta:
        model = OrderRequest
        fields = ["ingredient", "quantity", "note"]
        widgets = {
            "ingredient": forms.HiddenInput(),
        }


class SupplierProposalForm(forms.ModelForm):
    class Meta:
        model = SupplierProposal
        fields = ["offered_quantity", "offered_price", "message"]
class DeliveryForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = ["tracking_code", "note", "receipt", "photo"]