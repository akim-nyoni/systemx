from django import forms
from .models import FormTemplate, FormSection, ChecklistItem


class FormTemplateForm(forms.ModelForm):
    class Meta:
        model = FormTemplate
        fields = ['name', 'description', 'category', 'outlet', 'department', 'is_active', 'all_managers_access', 'assigned_users']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_users': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].widget.attrs['class'] = 'form-check-input'
        self.fields['all_managers_access'].widget.attrs['class'] = 'form-check-input'
        self.fields['category'].widget.attrs['class'] = 'form-select'
        self.fields['category'].required = False
        self.fields['category'].empty_label = '— No Category —'
        self.fields['outlet'].widget.attrs['class'] = 'form-select'
        self.fields['outlet'].required = False
        self.fields['outlet'].label = 'Outlet (blank = all restaurants)'
        self.fields['department'].widget.attrs['class'] = 'form-select'
        self.fields['department'].required = False
        self.fields['department'].label = 'Department (blank = all departments)'
