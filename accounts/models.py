from django.contrib.auth.models import AbstractUser
from django.db import models


class Department(models.Model):
    # These are just reference icons — no longer restrict the code field
    DEPT_ICONS = {
        'director':        '👔',
        'general_manager': '🏢',
        'front_of_house':  '🛎️',
        'bar':             '🍺',
        'waiters':         '🍽️',
        'floor_manager':   '📋',
        'bar_manager':     '🍹',
        'back_of_house':   '🍳',
        'kitchen_manager': '👨‍🍳',
        'stock_controller':'📦',
        'head_chef':       '🧑‍🍳',
        'coordinator':     '📌',
        'red_section':     '🔴',
        'yellow_section':  '🟡',
        'green_section':   '🟢',
        'blue_section':    '🔵',
        'white_section':   '⚪',
        'prep_section':    '🔪',
        'sushi_bar':       '🍣',
        'maintenance':     '🔧',
        'scullery':        '🧽',
        'general_cleaner': '🧹',
        'cleaning':        '🫧',
        'marketing':       '📣',
        'finance':         '💰',
    }

    name        = models.CharField(max_length=100, unique=True)
    code        = models.CharField(
        max_length=50, unique=True,
        help_text='Short identifier, auto-filled from name. Letters, numbers and underscores only.'
    )
    parent      = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='children', verbose_name='Parent Department'
    )
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    order       = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @property
    def full_path(self):
        if self.parent:
            return f"{self.parent.name} › {self.name}"
        return self.name

    @property
    def emoji(self):
        return self.DEPT_ICONS.get(self.code, '🏷️')


class Role(models.Model):
    """Flexible role — defines what a user can do."""
    name        = models.CharField(max_length=60, unique=True)
    description = models.TextField(blank=True)

    can_fill_forms         = models.BooleanField(default=True,  help_text='Can fill in checklists')
    can_view_reports       = models.BooleanField(default=False, help_text='Can view reports')
    can_view_all_reports   = models.BooleanField(default=False, help_text='Can view all departments reports')
    can_manage_forms       = models.BooleanField(default=False, help_text='Can build/edit form templates')
    can_manage_users       = models.BooleanField(default=False, help_text='Can create/edit users')
    can_delete_submissions = models.BooleanField(default=False, help_text='Can delete submissions')
    can_access_stock       = models.BooleanField(default=False, help_text='Can view and manage stock')
    can_manage_stock       = models.BooleanField(default=False, help_text='Can add/edit stock items, categories and locations')
    is_system_admin        = models.BooleanField(default=False, help_text='Full system access')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    custom_role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='users', verbose_name='Role'
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='users', verbose_name='Department'
    )
    branch = models.CharField(max_length=100, blank=True, default='Harare')
    phone  = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role_name})"

    @property
    def role_name(self):
        if self.is_superuser:
            return 'System Admin'
        return self.custom_role.name if self.custom_role else 'No Role'

    @property
    def dept_name(self):
        return self.department.name if self.department else '—'

    @property
    def dept_emoji(self):
        return self.department.emoji if self.department else '👤'

    @property
    def is_admin(self):
        if self.is_superuser:
            return True
        return self.custom_role.is_system_admin if self.custom_role else False

    # ── Permission shortcuts ──────────────────────────────
    @property
    def can_fill_forms(self):
        if self.is_admin: return True
        return self.custom_role.can_fill_forms if self.custom_role else False

    @property
    def can_view_reports(self):
        if self.is_admin: return True
        return self.custom_role.can_view_reports if self.custom_role else False

    @property
    def can_view_all_reports(self):
        if self.is_admin: return True
        return self.custom_role.can_view_all_reports if self.custom_role else False

    @property
    def can_manage_forms(self):
        if self.is_admin: return True
        return self.custom_role.can_manage_forms if self.custom_role else False

    @property
    def can_manage_users(self):
        if self.is_admin: return True
        return self.custom_role.can_manage_users if self.custom_role else False

    @property
    def can_delete_submissions(self):
        if self.is_admin: return True
        return self.custom_role.can_delete_submissions if self.custom_role else False

    @property
    def can_access_stock(self):
        if self.is_admin: return True
        return self.custom_role.can_access_stock if self.custom_role else False

    @property
    def can_manage_stock(self):
        if self.is_admin: return True
        return self.custom_role.can_manage_stock if self.custom_role else False

    @property
    def is_manager(self):
        return self.can_fill_forms

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    def get_visible_departments(self):
        """Returns department IDs this user is allowed to see in reports."""
        if self.is_admin:
            return None  # None means all
        if not self.department:
            return []
        # Collect own dept + all children
        dept_ids = [self.department.pk]
        dept_ids += list(self.department.children.values_list('pk', flat=True))
        return dept_ids
