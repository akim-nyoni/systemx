from django.contrib import admin
from .models import FormTemplate, FormSection, ChecklistItem, FormSubmission, ItemResponse


class FormSectionInline(admin.TabularInline):
    model = FormSection
    extra = 0


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0


@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'all_managers_access', 'created_at']
    list_filter = ['category', 'is_active']
    inlines = [FormSectionInline]


@admin.register(FormSection)
class FormSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'form', 'order']
    inlines = [ChecklistItemInline]


@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ['form', 'submitted_by', 'branch', 'shift', 'status', 'completion_percentage', 'created_at']
    list_filter = ['status', 'form', 'branch', 'shift']
    date_hierarchy = 'created_at'


@admin.register(ItemResponse)
class ItemResponseAdmin(admin.ModelAdmin):
    list_display = ['submission', 'item', 'value', 'answered_at']
    list_filter = ['value']
