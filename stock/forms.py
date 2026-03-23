from django import forms
from .models import StockItem, StockCategory, StockLocation, StockCount, StockMovement


# ── Custom widgets with data-outlet for JS filtering ──────────────

class DeptSelectWidget(forms.Select):
    """Adds data-outlet attribute to each department option for JS filtering."""
    def create_option(self, name, value, label, selected, index, **kwargs):
        option = super().create_option(name, value, label, selected, index, **kwargs)
        if value:
            try:
                from accounts.models import Department
                dept = Department.objects.select_related('outlet').get(pk=value)
                if dept.outlet:
                    option['attrs']['data-outlet'] = str(dept.outlet.pk)
            except Exception:
                pass
        return option


class LocationSelectWidget(forms.Select):
    """Adds data-outlet attribute to each location option for JS filtering."""
    def create_option(self, name, value, label, selected, index, **kwargs):
        option = super().create_option(name, value, label, selected, index, **kwargs)
        if value:
            try:
                loc = StockLocation.objects.select_related('outlet').get(pk=value)
                if loc.outlet:
                    option['attrs']['data-outlet'] = str(loc.outlet.pk)
            except Exception:
                pass
        return option


# ── Shared mixin: outlet/department cross-validation ──────────────

class OutletDeptMixin:
    """
    Mixin for forms with outlet + department fields.
    - Validates the selected department belongs to the selected outlet.
    - Sets up styled widgets and filtered querysets.
    """

    def _style_fields(self):
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 2})
            else:
                field.widget.attrs['class'] = 'form-control'

    def _setup_outlet_dept(self):
        from accounts.models import Outlet, Department
        if 'outlet' in self.fields:
            self.fields['outlet'].queryset = Outlet.objects.filter(is_active=True).order_by('order')
            self.fields['outlet'].empty_label = '— Select Outlet —'
            self.fields['outlet'].widget.attrs.update({
                'class': 'form-select',
                'id': 'id_outlet',
                'onchange': 'filterDeptByOutlet(this.value)',
            })
        if 'department' in self.fields:
            self.fields['department'].widget = DeptSelectWidget(
                attrs={'class': 'form-select', 'id': 'id_department'}
            )
            self.fields['department'].queryset = Department.objects.select_related('outlet').order_by(
                'outlet__order', 'order', 'name'
            )
            self.fields['department'].empty_label = '— Select Department —'
            self.fields['department'].required = False

    def clean(self):
        cleaned = super().clean()
        outlet = cleaned.get('outlet')
        department = cleaned.get('department')
        if outlet and department:
            if department.outlet and department.outlet != outlet:
                raise forms.ValidationError(
                    f'\u26a0\ufe0f Mismatch: "{department.name}" belongs to '
                    f'"{department.outlet.name}", not "{outlet.name}". '
                    f'Please select a department that belongs to the chosen outlet.'
                )
        return cleaned


# ── Stock Item ────────────────────────────────────────────────────

class StockItemForm(OutletDeptMixin, forms.ModelForm):
    class Meta:
        model = StockItem
        fields = [
            'name', 'sku', 'outlet', 'department', 'category', 'location',
            'unit', 'unit_cost', 'par_level', 'reorder_point', 'reorder_qty',
            'par_coverage_days', 'current_stock', 'notes', 'is_active',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()
        self._setup_outlet_dept()
        if self.instance and self.instance.pk and self.instance.outlet_id:
            self.fields['location'].queryset = StockLocation.objects.filter(
                outlet=self.instance.outlet, is_active=True
            )
        else:
            self.fields['location'].queryset = StockLocation.objects.filter(
                is_active=True
            ).select_related('outlet')
        self.fields['notes'].widget.attrs['rows'] = 2


# ── Stock Movement ────────────────────────────────────────────────

class StockMovementForm(OutletDeptMixin, forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['outlet', 'department', 'item', 'movement_type', 'quantity', 'unit_cost', 'reference', 'notes']

    def __init__(self, *args, **kwargs):
        user_outlet = kwargs.pop('user_outlet', None)
        super().__init__(*args, **kwargs)
        self._style_fields()
        self._setup_outlet_dept()
        if user_outlet:
            self.fields['item'].queryset = StockItem.objects.filter(
                is_active=True, outlet=user_outlet
            ).select_related('category', 'outlet')
            self.fields['outlet'].initial = user_outlet
        else:
            self.fields['item'].queryset = StockItem.objects.filter(
                is_active=True
            ).select_related('category', 'outlet')
        self.fields['unit_cost'].required = False
        self.fields['outlet'].required = False
        self.fields['department'].required = False

    def clean(self):
        cleaned = super().clean()
        outlet = cleaned.get('outlet')
        item = cleaned.get('item')
        if item and item.outlet and outlet and item.outlet != outlet:
            raise forms.ValidationError(
                f'\u26a0\ufe0f Mismatch: Item "{item.name}" belongs to "{item.outlet.name}" '
                f'but you selected outlet "{outlet.name}". Please match the outlet.'
            )
        return cleaned


# ── Stock Count ───────────────────────────────────────────────────

class StockCountForm(OutletDeptMixin, forms.ModelForm):
    class Meta:
        model = StockCount
        fields = ['outlet', 'department', 'location', 'count_date', 'shift', 'notes']

    def __init__(self, *args, **kwargs):
        user_outlet = kwargs.pop('user_outlet', None)
        super().__init__(*args, **kwargs)
        self._style_fields()
        self._setup_outlet_dept()
        self.fields['count_date'].widget = forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'}
        )
        self.fields['location'].widget = LocationSelectWidget(
            attrs={'class': 'form-select'}
        )
        if user_outlet:
            self.fields['location'].queryset = StockLocation.objects.filter(
                outlet=user_outlet, is_active=True
            )
            self.fields['outlet'].initial = user_outlet
        else:
            self.fields['location'].queryset = StockLocation.objects.filter(
                is_active=True
            ).select_related('outlet')
        self.fields['outlet'].required = False
        self.fields['department'].required = False

    def clean(self):
        cleaned = super().clean()
        outlet = cleaned.get('outlet')
        location = cleaned.get('location')
        if outlet and location and location.outlet and location.outlet != outlet:
            raise forms.ValidationError(
                f'\u26a0\ufe0f Mismatch: Location "{location.name}" belongs to '
                f'"{location.outlet.name}", not "{outlet.name}". '
                f'Please select a location that belongs to the chosen outlet.'
            )
        return cleaned


# ── Stock Location ────────────────────────────────────────────────

class StockLocationForm(OutletDeptMixin, forms.ModelForm):
    class Meta:
        model = StockLocation
        fields = ['name', 'outlet', 'department', 'description', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()
        self._setup_outlet_dept()
        self.fields['name'].widget.attrs['placeholder'] = 'e.g. Main Bar, Walk-in Fridge'
        self.fields['outlet'].required = False


# ── Stock Category ────────────────────────────────────────────────

class StockCategoryForm(forms.ModelForm):
    class Meta:
        model = StockCategory
        fields = ['name', 'code', 'description', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'e.g. Spirits, Seafood'})
        self.fields['code'].widget.attrs.update({'class': 'form-control', 'placeholder': 'e.g. spirits, seafood'})
        self.fields['code'].help_text = 'Short unique identifier — lowercase, letters and underscores only'
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 2})
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
