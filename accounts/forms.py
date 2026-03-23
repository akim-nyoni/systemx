from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Role, Department, Outlet


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'custom_role', 'outlet', 'department', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['custom_role'].widget.attrs['class'] = 'form-select'
        self.fields['custom_role'].label = 'Role'
        self.fields['custom_role'].required = True
        self.fields['department'].widget.attrs['class'] = 'form-select'
        self.fields['department'].label = 'Department'
        self.fields['department'].required = False
        self.fields['outlet'].widget.attrs['class'] = 'form-select'
        self.fields['outlet'].label = 'Outlet (Restaurant)'
        self.fields['outlet'].required = False


class UserEditForm(forms.ModelForm):
    """Admin edits any user — includes role and department."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'custom_role', 'outlet', 'department', 'phone', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
        self.fields['custom_role'].widget.attrs['class'] = 'form-select'
        self.fields['custom_role'].label = 'Role'
        self.fields['department'].widget.attrs['class'] = 'form-select'
        self.fields['department'].label = 'Department'
        self.fields['outlet'].widget.attrs['class'] = 'form-select'
        self.fields['outlet'].label = 'Outlet (Restaurant)'



    def clean(self):
        cleaned = super().clean()
        outlet = cleaned.get('outlet')
        department = cleaned.get('department')
        if outlet and department:
            if department.outlet and department.outlet != outlet:
                raise forms.ValidationError(
                    f'⚠️ Mismatch: "{department.name}" belongs to '
                    f'"{department.outlet.name}", not "{outlet.name}". '
                    f'Please select a department under the chosen outlet.'
                )
        return cleaned

class ProfileEditForm(forms.ModelForm):
    """User edits own profile — NO role, username, or department fields."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = [
            'name', 'description',
            'can_fill_forms', 'can_view_reports', 'can_view_all_reports',
            'can_manage_forms', 'can_manage_users', 'can_delete_submissions',
            'can_access_stock', 'can_manage_stock',
            'is_system_admin',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['class'] = 'form-control'
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 2})
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'parent', 'description', 'order', 'is_active']
        # 'code' is auto-generated from name — not shown to user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'e.g. Sushi Bar'})
        self.fields['name'].label = 'Department Name'
        self.fields['parent'].widget.attrs['class'] = 'form-select'
        self.fields['parent'].required = False
        self.fields['parent'].empty_label = '— None (top-level department) —'
        self.fields['parent'].label = 'Parent Department'
        self.fields['parent'].queryset = Department.objects.all().order_by('order', 'name')
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 2, 'placeholder': 'Optional description'})
        self.fields['order'].widget.attrs.update({'class': 'form-control', 'placeholder': '0'})
        self.fields['order'].label = 'Display Order'
        self.fields['order'].required = False
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'

    def save(self, commit=True):
        dept = super().save(commit=False)
        # Auto-generate code from name if not set or if name changed
        if not dept.code or (self.instance.pk and self.instance.name != dept.name):
            import re
            dept.code = re.sub(r'[^a-z0-9]+', '_', dept.name.lower()).strip('_')[:50]
            # Ensure uniqueness
            base_code = dept.code
            counter = 1
            while Department.objects.filter(code=dept.code).exclude(pk=dept.pk).exists():
                dept.code = f'{base_code}_{counter}'
                counter += 1
        if commit:
            dept.save()
        return dept


    def clean(self):
        cleaned = super().clean()
        outlet = cleaned.get('outlet')
        parent = cleaned.get('parent')
        if outlet and parent:
            if parent.outlet and parent.outlet != outlet:
                raise forms.ValidationError(
                    f'⚠️ Mismatch: Parent department "{parent.name}" belongs to '
                    f'"{parent.outlet.name}", not "{outlet.name}". '
                    f'Parent and child departments must be in the same outlet.'
                )
        return cleaned

class OutletForm(forms.ModelForm):
    class Meta:
        model = Outlet
        fields = ['name', 'code', 'address', 'phone', 'email', 'order', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 2})
            else:
                field.widget.attrs['class'] = 'form-control'
        self.fields['code'].help_text = 'Short unique code, e.g. sibili, phakalane, seventy_nine'
        self.fields['order'].help_text = 'Display order (1 = first)'
