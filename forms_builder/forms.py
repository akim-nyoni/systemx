from django import forms
from .models import FormTemplate, FormSection, ChecklistItem


class FormTemplateForm(forms.ModelForm):
    class Meta:
        model = FormTemplate
        fields = ['name', 'description', 'category', 'is_active', 'all_managers_access', 'assigned_users']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'assigned_users': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].widget.attrs['class'] = 'form-check-input'
        self.fields['all_managers_access'].widget.attrs['class'] = 'form-check-input'
