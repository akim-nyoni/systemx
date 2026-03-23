from django.contrib import admin
from .models import StockCategory, StockLocation, StockItem, StockCount, StockCountLine, StockMovement


@admin.register(StockCategory)
class StockCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']


@admin.register(StockLocation)
class StockLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'outlet', 'department', 'is_active']
    list_filter  = ['outlet', 'is_active']


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display  = ['name', 'outlet', 'category', 'location', 'unit', 'current_stock', 'par_level', 'stock_status']
    list_filter   = ['outlet', 'category', 'is_active']
    search_fields = ['name', 'sku']


@admin.register(StockCount)
class StockCountAdmin(admin.ModelAdmin):
    list_display = ['location', 'count_date', 'shift', 'status', 'conducted_by']
    list_filter  = ['location__outlet']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['item', 'movement_type', 'quantity', 'created_by', 'created_at']
    list_filter  = ['movement_type', 'item__outlet']
