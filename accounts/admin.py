from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ['emoji', 'name', 'code', 'parent', 'order', 'is_active']
    list_filter   = ['parent', 'is_active']
    ordering      = ['order', 'name']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'can_fill_forms', 'can_view_reports', 'can_view_all_reports',
                    'can_manage_forms', 'can_manage_users', 'is_system_admin']


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ['username', 'get_full_name', 'email', 'custom_role', 'department', 'branch', 'is_active']
    list_filter   = ['custom_role', 'department', 'is_active']
    fieldsets     = UserAdmin.fieldsets + (
        ('The Ambassador Profile', {'fields': ('custom_role', 'department', 'branch', 'phone', 'avatar')}),
    )
