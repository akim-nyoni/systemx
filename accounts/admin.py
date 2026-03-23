from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, Department, Outlet


@admin.register(Outlet)
class OutletAdmin(admin.ModelAdmin):
    list_display = ['emoji', 'name', 'code', 'order', 'is_active']
    ordering     = ['order']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ['emoji', 'name', 'outlet', 'parent', 'order', 'is_active']
    list_filter   = ['outlet', 'parent', 'is_active']
    ordering      = ['outlet__order', 'order', 'name']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'can_fill_forms', 'can_view_reports', 'can_view_all_reports',
                    'can_manage_forms', 'can_manage_users', 'can_access_stock', 'is_system_admin']


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ['username', 'get_full_name', 'email', 'custom_role', 'outlet', 'department', 'is_active']
    list_filter   = ['custom_role', 'outlet', 'department', 'is_active']
    fieldsets     = UserAdmin.fieldsets + (
        ('The Ambassador Profile', {'fields': ('custom_role', 'outlet', 'department', 'branch', 'phone', 'avatar')}),
    )
