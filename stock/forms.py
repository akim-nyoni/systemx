from django import forms
from .models import StockItem, StockCategory, StockLocation, StockCount, StockMovement


class StockItemForm(forms.ModelForm):
    class Meta:
        model = StockItem
        fields = [
            'name', 'sku', 'category', 'location', 'unit', 'unit_cost',
            'par_level', 'reorder_point', 'reorder_qty', 'par_coverage_days',
            'current_stock', 'notes', 'is_active',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
        self.fields['notes'].widget.attrs['rows'] = 2


class StockCountForm(forms.ModelForm):
    class Meta:
        model = StockCount
        fields = ['location', 'count_date', 'shift', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
        self.fields['count_date'].widget = forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'}
        )


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['item', 'movement_type', 'quantity', 'unit_cost', 'reference', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
        self.fields['notes'].widget.attrs['rows'] = 2
        self.fields['unit_cost'].required = False


class StockCategoryForm(forms.ModelForm):
    class Meta:
        model = StockCategory
        fields = ['name', 'code', 'description', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'e.g. Spirits, Seafood, Dry Goods'})
        self.fields['code'].widget.attrs.update({'class': 'form-control', 'placeholder': 'e.g. spirits, seafood, dry_goods'})
        self.fields['code'].help_text = 'Short unique identifier — lowercase, letters and underscores only'
        self.fields['description'].widget.attrs.update({'class': 'form-control', 'rows': 2})
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'


class StockLocationForm(forms.ModelForm):
    class Meta:
        model = StockLocation
        fields = ['name', 'department', 'description', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
