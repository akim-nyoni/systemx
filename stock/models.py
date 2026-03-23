"""
Stock Management Models for The Ambassador
-------------------------------------------
StockCategory      — Beer, Spirits, Wine, Food, Cleaning, etc.
StockItem          — Each product with unit, PAR level, reorder point
StockLocation      — Bar, Kitchen, Cellar, Dry Store, etc.
StockCount         — A stock-take session (date, location, done by)
StockCountLine     — Actual counted qty for each item in a count
StockMovement      — Deliveries, transfers, wastage, adjustments
PAR Level Logic    — PAR = average daily usage × coverage days
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class StockCategory(models.Model):
    CATEGORY_ICONS = {
        'beer':       '🍺',
        'spirits':    '🥃',
        'wine':       '🍷',
        'soft_drink': '🥤',
        'juice':      '🧃',
        'dairy':      '🥛',
        'meat':       '🥩',
        'seafood':    '🦐',
        'produce':    '🥦',
        'dry_goods':  '🌾',
        'sauces':     '🫙',
        'cleaning':   '🧹',
        'packaging':  '📦',
        'other':      '📋',
    }

    name        = models.CharField(max_length=100, unique=True)
    code        = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Stock Categories'

    def __str__(self):
        return self.name

    @property
    def emoji(self):
        return self.CATEGORY_ICONS.get(self.code, '📋')


class StockLocation(models.Model):
    name        = models.CharField(max_length=100)
    outlet      = models.ForeignKey(
        'accounts.Outlet', on_delete=models.CASCADE,
        null=True, blank=True, related_name='stock_locations',
        help_text='Which restaurant this storage location belongs to'
    )
    department  = models.ForeignKey(
        'accounts.Department', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='stock_locations'
    )
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)

    class Meta:
        ordering = ['outlet__order', 'name']
        unique_together = [['outlet', 'name']]

    def __str__(self):
        if self.outlet:
            return f"{self.name} ({self.outlet.short_name})"
        return self.name


class StockItem(models.Model):
    UNIT_CHOICES = [
        ('each',    'Each'),
        ('bottle',  'Bottle'),
        ('can',     'Can'),
        ('kg',      'Kilogram (kg)'),
        ('g',       'Gram (g)'),
        ('litre',   'Litre (L)'),
        ('ml',      'Millilitre (ml)'),
        ('case',    'Case'),
        ('box',     'Box'),
        ('bag',     'Bag'),
        ('roll',    'Roll'),
        ('portion', 'Portion'),
    ]

    name            = models.CharField(max_length=200)
    sku             = models.CharField(max_length=50, blank=True)
    outlet          = models.ForeignKey(
        'accounts.Outlet', on_delete=models.CASCADE,
        null=True, blank=True, related_name='stock_items',
        help_text='Which restaurant this item belongs to'
    )
    department      = models.ForeignKey(
        'accounts.Department', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='stock_items',
        help_text='Which department manages this item'
    )
    category        = models.ForeignKey(StockCategory, on_delete=models.PROTECT, related_name='items')
    location        = models.ForeignKey(StockLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    unit            = models.CharField(max_length=20, choices=UNIT_CHOICES, default='each')
    unit_cost       = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # PAR level management
    par_level       = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Ideal stock level — what should be on shelf at start of day'
    )
    reorder_point   = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Trigger reorder when stock falls below this level'
    )
    reorder_qty     = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Standard quantity to order when reorder is triggered'
    )
    # Average daily usage — updated automatically from count history
    avg_daily_usage = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Auto-calculated average daily usage from stock counts'
    )
    par_coverage_days = models.PositiveIntegerField(
        default=3,
        help_text='How many days of stock PAR should cover (e.g. 3 = 3-day buffer)'
    )

    current_stock   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active       = models.BooleanField(default=True)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"

    @property
    def stock_status(self):
        if self.current_stock <= 0:
            return 'out'
        if self.current_stock <= self.reorder_point:
            return 'critical'
        if self.current_stock < self.par_level:
            return 'low'
        return 'ok'

    @property
    def stock_status_label(self):
        return {
            'out':      '🔴 Out of Stock',
            'critical': '🟠 Critical — Order Now',
            'low':      '🟡 Below PAR',
            'ok':       '🟢 OK',
        }.get(self.stock_status, '—')

    @property
    def calculated_par(self):
        """PAR = avg daily usage × coverage days"""
        if self.avg_daily_usage > 0:
            return round(self.avg_daily_usage * self.par_coverage_days, 2)
        return self.par_level

    @property
    def order_qty_needed(self):
        """How much to order to reach PAR level."""
        needed = self.calculated_par - self.current_stock
        return max(Decimal('0'), needed)

    @property
    def variance_pct(self):
        """% variance from PAR level."""
        if self.par_level <= 0:
            return None
        return round(((self.current_stock - self.par_level) / self.par_level) * 100, 1)

    def recalculate_avg_usage(self):
        """Recalculate average daily usage from the last 30 days of count data."""
        from django.db.models import Avg
        movements = StockMovement.objects.filter(
            item=self,
            movement_type='usage',
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        )
        total_used = sum(m.quantity for m in movements)
        days = 30
        if total_used > 0:
            self.avg_daily_usage = round(Decimal(str(total_used)) / Decimal(str(days)), 4)
            self.par_level = self.calculated_par
            self.save(update_fields=['avg_daily_usage', 'par_level'])


class StockCount(models.Model):
    STATUS_DRAFT     = 'draft'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_DRAFT,     'Draft'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    location    = models.ForeignKey(StockLocation, on_delete=models.PROTECT, related_name='counts')
    outlet      = models.ForeignKey(
        'accounts.Outlet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_counts'
    )
    department  = models.ForeignKey(
        'accounts.Department', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_counts'
    )
    count_date  = models.DateField(default=timezone.now)
    shift       = models.CharField(max_length=10, choices=[('opening','Opening'),('closing','Closing'),('mid','Mid-shift')], default='closing')
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    conducted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='stock_counts')
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-count_date', '-created_at']

    def __str__(self):
        return f"{self.location} — {self.count_date} ({self.shift})"

    @property
    def total_items(self):
        return self.lines.count()

    @property
    def counted_items(self):
        return self.lines.exclude(counted_qty=None).count()

    @property
    def items_below_par(self):
        return self.lines.filter(variance__lt=0).count()

    @property
    def completion_pct(self):
        if self.total_items == 0:
            return 0
        return round((self.counted_items / self.total_items) * 100)

    def complete(self):
        """Mark count as complete and update current stock levels.
        The counted_qty IS the new stock level — set it directly.
        Movement records are created for audit trail only (skip_stock_update=True).
        """
        for line in self.lines.all():
            if line.counted_qty is not None:
                old_stock = line.item.current_stock
                # Directly set stock to what was physically counted
                line.item.current_stock = line.counted_qty
                line.item.save(update_fields=['current_stock'])
                # Record audit movement — but DON'T let movement.save() adjust stock again
                variance = line.counted_qty - old_stock
                if variance != 0:
                    movement_type = 'usage' if variance < 0 else 'adjustment'
                    m = StockMovement(
                        item=line.item,
                        movement_type=movement_type,
                        quantity=abs(variance),
                        reference=f"Stock count {self.count_date} ({self.get_shift_display()})",
                        notes=f"Counted: {line.counted_qty}, Previous: {old_stock}",
                        created_by=self.conducted_by,
                    )
                    m._skip_stock_update = True  # prevent double-adjustment
                    m.save()
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.save()


class StockCountLine(models.Model):
    count       = models.ForeignKey(StockCount, on_delete=models.CASCADE, related_name='lines')
    item        = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name='count_lines')
    expected_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                       help_text='Stock level expected based on last count + deliveries - usage')
    counted_qty  = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    variance     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                       help_text='counted - expected')
    notes        = models.TextField(blank=True)

    class Meta:
        ordering = ['item__category__name', 'item__name']
        unique_together = ['count', 'item']

    def save(self, *args, **kwargs):
        if self.counted_qty is not None:
            self.variance = self.counted_qty - self.expected_qty
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name}: {self.counted_qty} / {self.expected_qty}"

    @property
    def variance_status(self):
        if self.variance is None:
            return 'pending'
        if self.variance < -1:
            return 'shortage'
        if self.variance > 1:
            return 'surplus'
        return 'ok'

    @property
    def below_par(self):
        if self.counted_qty is None:
            return False
        return self.counted_qty < self.item.par_level


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('delivery',    'Delivery / Received'),
        ('usage',       'Usage / Consumed'),
        ('wastage',     'Wastage / Spoilage'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out','Transfer Out'),
        ('adjustment',  'Manual Adjustment'),
        ('return',      'Return to Supplier'),
    ]

    item            = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name='movements')
    outlet          = models.ForeignKey(
        'accounts.Outlet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_movements'
    )
    department      = models.ForeignKey(
        'accounts.Department', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='stock_movements'
    )
    movement_type   = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity        = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reference       = models.CharField(max_length=200, blank=True,
                                       help_text='Invoice number, supplier name, reason, etc.')
    notes           = models.TextField(blank=True)
    created_by      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='stock_movements')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} — {self.item.name} x{self.quantity}"

    @property
    def is_inbound(self):
        return self.movement_type in ('delivery', 'transfer_in', 'adjustment', 'return')

    @property
    def total_value(self):
        return self.quantity * self.unit_cost

    def save(self, *args, **kwargs):
        skip = getattr(self, '_skip_stock_update', False)
        super().save(*args, **kwargs)
        if not skip:
            # Update current stock on item
            item = self.item
            item.refresh_from_db(fields=['current_stock'])
            if self.is_inbound:
                item.current_stock += self.quantity
            else:
                item.current_stock = max(Decimal('0'), item.current_stock - self.quantity)
            item.save(update_fields=['current_stock'])
