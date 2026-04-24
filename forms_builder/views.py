from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from .models import FormTemplate, FormSection, ChecklistItem, FormSubmission, ItemResponse


def require_admin(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            messages.error(request, 'Administrator access required.')
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ─── Form Template Management (Admin only) ───────────────────────────────────

@login_required
@require_admin
def template_list(request):
    templates = FormTemplate.objects.prefetch_related('sections__items').all()
    return render(request, 'forms_builder/template_list.html', {'templates': templates})


@login_required
@require_admin
def template_create(request):
    from .forms import FormTemplateForm
    if request.method == 'POST':
        form = FormTemplateForm(request.POST)
        if form.is_valid():
            tmpl = form.save(commit=False)
            tmpl.created_by = request.user
            tmpl.save()
            form.save_m2m()
            messages.success(request, f'Form "{tmpl.name}" created.')
            return redirect('forms_builder:template_builder', pk=tmpl.pk)
    else:
        form = FormTemplateForm()
    return render(request, 'forms_builder/template_form.html', {'form': form, 'title': 'Create Form Template'})


@login_required
@require_admin
def template_edit(request, pk):
    from .forms import FormTemplateForm
    tmpl = get_object_or_404(FormTemplate, pk=pk)
    if request.method == 'POST':
        form = FormTemplateForm(request.POST, instance=tmpl)
        if form.is_valid():
            form.save()
            messages.success(request, 'Form updated.')
            return redirect('forms_builder:template_list')
    else:
        form = FormTemplateForm(instance=tmpl)
    return render(request, 'forms_builder/template_form.html', {'form': form, 'title': f'Edit: {tmpl.name}', 'tmpl': tmpl})


@login_required
@require_admin
def template_builder(request, pk):
    """Visual drag-and-drop builder for form sections and items"""
    tmpl = get_object_or_404(FormTemplate, pk=pk)
    sections = tmpl.sections.prefetch_related('items').all()
    return render(request, 'forms_builder/template_builder.html', {
        'tmpl': tmpl,
        'sections': sections,
    })


@login_required
@require_admin
def section_create(request, form_pk):
    tmpl = get_object_or_404(FormTemplate, pk=form_pk)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if title:
            order = tmpl.sections.count()
            section = FormSection.objects.create(form=tmpl, title=title, order=order)
            return JsonResponse({'id': section.pk, 'title': section.title, 'order': section.order})
    return JsonResponse({'error': 'Invalid'}, status=400)


@login_required
@require_admin
def section_delete(request, pk):
    section = get_object_or_404(FormSection, pk=pk)
    form_pk = section.form.pk
    section.delete()
    return JsonResponse({'ok': True})


@login_required
@require_admin
def item_create(request, section_pk):
    section = get_object_or_404(FormSection, pk=section_pk)
    if request.method == 'POST':
        label = request.POST.get('label', '').strip()
        response_type = request.POST.get('response_type', 'yes_no')
        requires_comment = request.POST.get('requires_comment_on_no') == 'true'
        requires_image = request.POST.get('requires_image_on_no') == 'true'
        if label:
            order = section.items.count()
            item = ChecklistItem.objects.create(
                section=section,
                label=label,
                response_type=response_type,
                requires_comment_on_no=requires_comment,
                requires_image_on_no=requires_image,
                order=order
            )
            return JsonResponse({
                'id': item.pk,
                'label': item.label,
                'response_type': item.response_type,
                'response_type_display': item.get_response_type_display(),
            })
    return JsonResponse({'error': 'Invalid'}, status=400)


@login_required
@require_admin
def item_delete(request, pk):
    item = get_object_or_404(ChecklistItem, pk=pk)
    item.delete()
    return JsonResponse({'ok': True})


# ─── Form Filling (Managers) ──────────────────────────────────────────────────

@login_required
def my_forms(request):
    """List forms the current user has access to"""
    if request.user.is_admin:
        templates = FormTemplate.objects.filter(is_active=True)
    else:
        templates = FormTemplate.objects.filter(is_active=True).filter(
            models.Q(all_managers_access=True) |
            models.Q(assigned_users=request.user)
        ).distinct()

    # Recent submissions by this user
    recent = FormSubmission.objects.filter(
        submitted_by=request.user
    ).select_related('form').order_by('-created_at')[:10]

    return render(request, 'forms_builder/my_forms.html', {
        'templates': templates,
        'recent': recent,
    })


@login_required
def fill_form(request, pk):
    """Start or continue filling a form"""
    tmpl = get_object_or_404(FormTemplate, pk=pk, is_active=True)

    if not tmpl.can_user_access(request.user):
        messages.error(request, 'You do not have access to this form.')
        return redirect('forms_builder:my_forms')

    # Check for existing draft
    draft = FormSubmission.objects.filter(
        form=tmpl,
        submitted_by=request.user,
        status=FormSubmission.STATUS_DRAFT
    ).first()

    if not draft:
        shift = request.GET.get('shift', 'day')
        draft = FormSubmission.objects.create(
            form=tmpl,
            submitted_by=request.user,
            outlet=request.user.outlet,
            department=request.user.department,
            shift=shift,
            status=FormSubmission.STATUS_DRAFT
        )
        # Pre-create all response slots
        for section in tmpl.sections.prefetch_related('items'):
            for item in section.items.filter(is_active=True):
                ItemResponse.objects.get_or_create(submission=draft, item=item)

    sections = tmpl.sections.prefetch_related(
        'items__responses'
    ).filter(items__is_active=True).distinct()

  # Build responses map with safe image URL handling
    responses_map = {}
    for r in draft.responses.all():
        responses_map[r.item_id] = r

    return render(request, 'forms_builder/fill_form.html', {
        'tmpl': tmpl,
        'submission': draft,
        'sections': sections,
        'responses_map': responses_map,
    })


@login_required
def save_response(request, submission_pk):
    """AJAX: Save a single item response"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    submission = get_object_or_404(FormSubmission, pk=submission_pk, submitted_by=request.user)
    if submission.status == FormSubmission.STATUS_SUBMITTED:
        return JsonResponse({'error': 'Form already submitted'}, status=400)

    item_id = request.POST.get('item_id')
    value = request.POST.get('value', '')
    comment = request.POST.get('comment', '')
    image_file = request.FILES.get('image')

    try:
        response = ItemResponse.objects.get(submission=submission, item_id=item_id)
        response.value = value
        response.comment = comment
        if image_file:
            response.image = image_file
        response.save()
        submission.update_stats()
        return JsonResponse({
            'ok': True,
            'completion': submission.completion_percentage,
            'has_image': bool(response.image),
        })
    except ItemResponse.DoesNotExist:
        return JsonResponse({'error': 'Response not found'}, status=404)


@login_required
def submit_form(request, submission_pk):
    """Final submission of a form"""
    submission = get_object_or_404(FormSubmission, pk=submission_pk, submitted_by=request.user)

    if submission.status == FormSubmission.STATUS_SUBMITTED:
        messages.info(request, 'This form has already been submitted.')
        return redirect('forms_builder:my_forms')

    # Check required items
    missing = []
    for response in submission.responses.select_related('item'):
        if response.item.is_required and not response.value:
            missing.append(response.item.label)

    if missing and request.POST.get('force') != '1':
        messages.warning(request, f'{len(missing)} required items are incomplete. Review before submitting.')
        return redirect('forms_builder:fill_form', pk=submission.form_id)

    submission.submit()
    submission.update_stats()
    messages.success(request, f'✅ "{submission.form.name}" submitted successfully!')
    return redirect('forms_builder:submission_detail', pk=submission.pk)


@login_required
def submission_detail(request, pk):
    """View a completed submission"""
    submission = get_object_or_404(FormSubmission, pk=pk)

    # Access: own submission, admin, or report viewer
    if submission.submitted_by != request.user and not request.user.can_view_reports:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    # Build responses map keyed by item_id
    responses_map = {r.item_id: r for r in submission.responses.select_related('item__section')}

    # Build sections with items + responses pre-attached for easy template rendering
    sections_data = []
    for section in submission.form.sections.prefetch_related('items').order_by('order'):
        items_data = []
        for item in section.items.filter(is_active=True).order_by('order'):
            resp = responses_map.get(item.pk)
            items_data.append({'item': item, 'resp': resp})
        if items_data:
            sections_data.append({'section': section, 'items': items_data})

    flagged = [
        {'item': r.item, 'resp': r}
        for r in submission.responses.filter(value__iexact='no').select_related('item__section')
    ]

    return render(request, 'forms_builder/submission_detail.html', {
        'submission': submission,
        'sections_data': sections_data,
        'flagged': flagged,
    })


# Fix the import
from django.db import models as dj_models

def my_forms(request):
    from django.db.models import Q
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    if request.user.is_admin:
        templates = FormTemplate.objects.filter(is_active=True)
    else:
        user_dept = request.user.department
        # Base access: all_managers_access or explicitly assigned
        qs = FormTemplate.objects.filter(is_active=True).filter(
            Q(all_managers_access=True) | Q(assigned_users=request.user)
        )
        # Restrict to forms matching user's department (or no department set)
        if user_dept:
            qs = qs.filter(Q(department__isnull=True) | Q(department=user_dept) | Q(department=user_dept.parent))
        templates = qs.distinct()

    recent = FormSubmission.objects.filter(
        submitted_by=request.user
    ).select_related('form').order_by('-created_at')[:10]

    return render(request, 'forms_builder/my_forms.html', {
        'templates': templates,
        'recent': recent,
    })

my_forms = login_required(my_forms)


# ─── Delete Template ─────────────────────────────────────────────

@login_required
@require_admin
def template_delete(request, pk):
    tmpl = get_object_or_404(FormTemplate, pk=pk)
    submission_count = tmpl.submissions.count()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'delete_all':
            name = tmpl.name
            # Must delete submissions first because FormSubmission.form uses PROTECT
            # Delete item responses first, then submissions, then the template
            with transaction.atomic():
                for submission in tmpl.submissions.all():
                    submission.responses.all().delete()
                tmpl.submissions.all().delete()
                tmpl.delete()
            messages.success(request, f'Form "{name}" and all {submission_count} submission(s) permanently deleted.')
            return redirect('forms_builder:template_list')

        elif action == 'delete_template_only' and submission_count == 0:
            name = tmpl.name
            tmpl.delete()
            messages.success(request, f'Form "{name}" deleted.')
            return redirect('forms_builder:template_list')

        else:
            messages.error(request, 'Invalid action.')

    return render(request, 'forms_builder/template_delete.html', {
        'tmpl': tmpl,
        'submission_count': submission_count,
    })


# ─── Form Categories CRUD ─────────────────────────────────────────

from .models import FormCategory

@login_required
@require_admin
def fb_category_list(request):
    categories = FormCategory.objects.annotate(
        tpl_count=Count('templates')
    ).order_by('order', 'name')
    return render(request, 'forms_builder/fb_category_list.html', {'categories': categories})


@login_required
@require_admin
def category_create(request):
    if request.method == 'POST':
        name  = request.POST.get('name', '').strip()
        code  = request.POST.get('code', '').strip()
        desc  = request.POST.get('description', '').strip()
        order = request.POST.get('order', 0)
        errors = []
        if not name:
            errors.append('Name is required.')
        if not code:
            errors.append('Code is required.')
        elif FormCategory.objects.filter(code=code).exists():
            errors.append(f'Code "{code}" is already in use.')
        if not errors:
            FormCategory.objects.create(name=name, code=code, description=desc, order=order)
            messages.success(request, f'Category "{name}" created.')
            return redirect('forms_builder:fb_category_list')
        for e in errors:
            messages.error(request, e)
    return render(request, 'forms_builder/category_form.html', {'title': 'Add Category', 'action': 'create'})


@login_required
@require_admin
def category_edit(request, pk):
    cat = get_object_or_404(FormCategory, pk=pk)
    if request.method == 'POST':
        name  = request.POST.get('name', '').strip()
        code  = request.POST.get('code', '').strip()
        desc  = request.POST.get('description', '').strip()
        order = request.POST.get('order', 0)
        errors = []
        if not name:
            errors.append('Name is required.')
        if not code:
            errors.append('Code is required.')
        elif FormCategory.objects.filter(code=code).exclude(pk=pk).exists():
            errors.append(f'Code "{code}" is already in use by another category.')
        if not errors:
            cat.name = name
            cat.code = code
            cat.description = desc
            cat.order = order
            cat.is_active = 'is_active' in request.POST
            cat.save()
            messages.success(request, f'Category "{name}" updated.')
            return redirect('forms_builder:fb_category_list')
        for e in errors:
            messages.error(request, e)
    return render(request, 'forms_builder/category_form.html', {
        'title': f'Edit Category: {cat.name}',
        'action': 'edit',
        'cat': cat,
    })


@login_required
@require_admin
def category_delete(request, pk):
    cat = get_object_or_404(FormCategory, pk=pk)
    form_count = cat.templates.count()
    if request.method == 'POST':
        if form_count > 0:
            # Unlink templates from this category before deleting
            cat.templates.all().update(category=None)
        name = cat.name
        cat.delete()
        messages.success(request, f'Category "{name}" deleted.')
        return redirect('forms_builder:fb_category_list')
    return render(request, 'forms_builder/category_delete.html', {
        'cat': cat,
        'form_count': form_count,
    })
