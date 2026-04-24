from django.db import models
from django.conf import settings
from django.utils import timezone


class FormCategory(models.Model):
    """User-manageable categories for form templates."""
    name       = models.CharField(max_length=100, unique=True)
    code       = models.SlugField(max_length=50, unique=True, help_text='Short unique key, e.g. opening, bar, kitchen')
    description= models.TextField(blank=True)
    order      = models.PositiveIntegerField(default=0)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Form Category'
        verbose_name_plural = 'Form Categories'

    def __str__(self):
        return self.name

    @property
    def form_count(self):
        return self.templates.count()


class FormTemplate(models.Model):
    """A checklist form template (e.g. Management Checklist, Bar Checklist)"""

    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category    = models.ForeignKey(
        FormCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='templates', verbose_name='Category',
        help_text='Select a category — manage categories from Form Categories in the sidebar'
    )
    outlet      = models.ForeignKey(
        'accounts.Outlet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='form_templates', verbose_name='Outlet',
        help_text='Which restaurant this form belongs to (blank = all outlets)'
    )
    department  = models.ForeignKey(
        'accounts.Department', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='forms', verbose_name='Department',
        help_text='Which department this checklist belongs to'
    )
    is_active   = models.BooleanField(default=True)
    created_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_forms')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    assigned_users      = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='assigned_forms')
    all_managers_access = models.BooleanField(default=True)

    class Meta:
        ordering = ['category__name', 'name']
        verbose_name = 'Form Template'

    def __str__(self):
        return self.name

    @property
    def category_name(self):
        return self.category.name if self.category else 'Uncategorised'

    def can_user_access(self, user):
        if user.is_admin:
            return True
        # If form has a department, user must be in that department
        if self.department and user.department:
            if self.department != user.department:
                return False
        if self.all_managers_access and user.is_manager:
            return True
        return self.assigned_users.filter(pk=user.pk).exists()


class FormSection(models.Model):
    """A section/group within a form (e.g. FOH, Bar, Kitchen)"""
    form = models.ForeignKey(FormTemplate, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.form.name} > {self.title}"


class ChecklistItem(models.Model):
    """An individual checklist item/question"""
    RESPONSE_TYPE_YES_NO = 'yes_no'
    RESPONSE_TYPE_TEXT = 'text'
    RESPONSE_TYPE_NUMBER = 'number'
    RESPONSE_TYPE_CHOICE = 'choice'

    RESPONSE_TYPE_CHOICES = [
        (RESPONSE_TYPE_YES_NO, 'Yes / No'),
        (RESPONSE_TYPE_TEXT, 'Text Input'),
        (RESPONSE_TYPE_NUMBER, 'Number'),
        (RESPONSE_TYPE_CHOICE, 'Multiple Choice'),
    ]

    section = models.ForeignKey(FormSection, on_delete=models.CASCADE, related_name='items')
    label = models.CharField(max_length=500)
    response_type = models.CharField(max_length=20, choices=RESPONSE_TYPE_CHOICES, default=RESPONSE_TYPE_YES_NO)
    is_required = models.BooleanField(default=True)
    requires_comment_on_no = models.BooleanField(default=True, help_text='If Yes/No and answered No, require explanation')
    requires_image_on_no = models.BooleanField(default=False, help_text='If answered No, allow image upload')
    choices_text = models.TextField(blank=True, help_text='Comma separated choices for multiple choice type')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.label

    def get_choices(self):
        if self.choices_text:
            return [c.strip() for c in self.choices_text.split(',') if c.strip()]
        return []


class FormSubmission(models.Model):
    """A completed submission of a form by a manager"""
    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
    ]

    form = models.ForeignKey(FormTemplate, on_delete=models.PROTECT, related_name='submissions')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='submissions')
    outlet = models.ForeignKey(
        'accounts.Outlet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='submissions'
    )
    department = models.ForeignKey(
        'accounts.Department', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='submissions'
    )
    shift = models.CharField(max_length=20, choices=[('day', 'Day'), ('night', 'Night'), ('full', 'Full Day')], default='day')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text='Overall notes for this submission')

    # Computed fields (updated on save)
    total_items = models.PositiveIntegerField(default=0)
    completed_items = models.PositiveIntegerField(default=0)
    no_responses = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Form Submission'

    def __str__(self):
        return f"{self.form.name} - {self.submitted_by.display_name} - {self.created_at.strftime('%d %b %Y')}"

    @property
    def completion_percentage(self):
        if self.total_items == 0:
            return 0
        return round((self.completed_items / self.total_items) * 100)

    def submit(self):
        self.status = self.STATUS_SUBMITTED
        self.submitted_at = timezone.now()
        self.save()

    def update_stats(self):
        responses = self.responses.all()
        self.total_items = responses.count()
        self.completed_items = responses.exclude(value='').exclude(value__isnull=True).count()
        self.no_responses = responses.filter(value__iexact='no').count()
        self.save(update_fields=['total_items', 'completed_items', 'no_responses'])


class ItemResponse(models.Model):
    """A single item response within a submission"""
    submission = models.ForeignKey(FormSubmission, on_delete=models.CASCADE, related_name='responses')
    item = models.ForeignKey(ChecklistItem, on_delete=models.PROTECT, related_name='responses')
    value = models.TextField(blank=True)  # 'Yes', 'No', or free text / number
    comment = models.TextField(blank=True, help_text='Explanation, especially required on No responses')
    image = models.ImageField(upload_to='responses/%Y/%m/', blank=True, null=True)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['submission', 'item']
        ordering = ['item__order']

    def __str__(self):
        return f"{self.item.label}: {self.value}"

    @property
    def is_yes(self):
        return self.value.strip().lower() == 'yes'

    @property
    def is_no(self):
        return self.value.strip().lower() == 'no'

    @property
    def needs_attention(self):
        return self.is_no and self.item.response_type == ChecklistItem.RESPONSE_TYPE_YES_NO
