from django import forms

class AdminColumnPreferenceForm(forms.Form):
    columns = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )