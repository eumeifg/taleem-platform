"""
forms for payment gateway admin.
"""
from django import forms


class AddVouchersForm(forms.Form):
    """
    Form for adding vouchers in bulk.
    """
    name = forms.CharField(required=True, max_length=128, widget=forms.TextInput(attrs={'class': 'vTextField'}))
    discount = forms.DecimalField(required=True, decimal_places=2, max_digits=12)
    count = forms.IntegerField(required=True, min_value=0)
