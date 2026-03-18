from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime, date as date_type
from forms_builder.models import FormSubmission, FormTemplate, ItemResponse
from accounts.models import User


def _parse_date(value):
    """Safely parse a YYYY-MM-DD string into a date object. Returns None on failure."""
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), '%Y-%m-%d').date()
    except (ValueError, TypeError, AttributeError):
        return None


def _apply_filters(submissions, request, params):
    """Apply common report filters to a submissions queryset."""
    from django.utils import timezone as tz
    import pytz

    staff_id        = params.get('staff')
    form_id         = params.get('form')
    dept_id         = params.get('dept')
    date_from       = _parse_date(params.get('date_from'))
    date_to         = _parse_date(params.get('date_to'))
    response_filter = params.get('response')
    branch          = params.get('branch', '').strip()

    # Admins see all; others scoped to their department tree
    visible_depts = request.user.get_visible_departments()
    if visible_depts is None:
        pass  # admin — no restriction
    elif not request.user.can_view_all_reports:
        submissions = submissions.filter(submitted_by=request.user)
    elif visible_depts:
        submissions = submissions.filter(submitted_by__department_id__in=visible_depts)
    else:
        submissions = submissions.filter(submitted_by=request.user)

    if staff_id:
        try:
            submissions = submissions.filter(submitted_by_id=int(staff_id))
        except (ValueError, TypeError):
            pass

    if form_id:
        try:
            submissions = submissions.filter(form_id=int(form_id))
        except (ValueError, TypeError):
            pass

    if dept_id:
        try:
            submissions = submissions.filter(submitted_by__department_id=int(dept_id))
        except (ValueError, TypeError):
            pass

    if date_from or date_to:
        from datetime import time as time_type
        try:
            local_tz = pytz.timezone('Africa/Harare')
        except Exception:
            local_tz = tz.get_current_timezone()
        if date_from:
            start_local = datetime.combine(date_from, time_type.min)
            start_aware = local_tz.localize(start_local)
            submissions = submissions.filter(submitted_at__gte=start_aware)
        if date_to:
            end_local = datetime.combine(date_to, time_type.max)
            end_aware = local_tz.localize(end_local)
            submissions = submissions.filter(submitted_at__lte=end_aware)

    if branch:
        submissions = submissions.filter(branch__icontains=branch)
    if response_filter == 'no':
        submissions = submissions.filter(no_responses__gt=0)
    elif response_filter == 'perfect':
        submissions = submissions.filter(no_responses=0)

    return submissions


@login_required
def home(request):
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    if request.user.can_view_all_reports:
        total_submissions = FormSubmission.objects.filter(status='submitted').count()
        today_submissions = FormSubmission.objects.filter(status='submitted', submitted_at__date=today).count()
        week_submissions = FormSubmission.objects.filter(status='submitted', submitted_at__date__gte=week_start).count()
        flagged_count = ItemResponse.objects.filter(
            value__iexact='no', submission__status='submitted', submission__submitted_at__date__gte=week_start
        ).count()
        recent_submissions = FormSubmission.objects.filter(status='submitted').select_related('form', 'submitted_by').order_by('-submitted_at')[:8]
        active_users = User.objects.filter(is_active=True).count()
        active_forms = FormTemplate.objects.filter(is_active=True).count()
        chart_data = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            count = FormSubmission.objects.filter(status='submitted', submitted_at__date=d).count()
            chart_data.append({'date': d.strftime('%a %d'), 'count': count})
        context = {
            'is_full_dashboard': True,
            'total_submissions': total_submissions,
            'today_submissions': today_submissions,
            'week_submissions': week_submissions,
            'flagged_count': flagged_count,
            'recent_submissions': recent_submissions,
            'active_users': active_users,
            'active_forms': active_forms,
            'chart_data': chart_data,
        }
    else:
        my_submissions = FormSubmission.objects.filter(submitted_by=request.user)
        total = my_submissions.filter(status='submitted').count()
        today_count = my_submissions.filter(status='submitted', submitted_at__date=today).count()
        drafts = my_submissions.filter(status='draft').count()
        my_flagged = ItemResponse.objects.filter(
            submission__submitted_by=request.user, submission__status='submitted',
            value__iexact='no', submission__submitted_at__date__gte=week_start
        ).count()
        recent_submissions = my_submissions.select_related('form').order_by('-created_at')[:8]
        context = {
            'is_full_dashboard': False,
            'total_submissions': total,
            'today_submissions': today_count,
            'drafts': drafts,
            'flagged_count': my_flagged,
            'recent_submissions': recent_submissions,
        }

    return render(request, 'dashboard/home.html', context)


@login_required
def reports(request):
    if not request.user.can_view_reports:
        messages.error(request, 'You do not have permission to view reports.')
        return redirect('dashboard:home')

    params = request.GET
    submissions = FormSubmission.objects.filter(status='submitted').select_related('form', 'submitted_by')
    submissions = _apply_filters(submissions, request, params).order_by('-submitted_at')

    total   = submissions.count()
    flagged = submissions.filter(no_responses__gt=0).count()
    perfect = submissions.filter(no_responses=0).count()

    flagged_items = ItemResponse.objects.filter(
        value__iexact='no', submission__in=submissions
    ).select_related('submission__submitted_by', 'submission__form', 'item__section')

    staff_list = User.objects.filter(is_active=True).select_related('department').order_by('first_name', 'username') if request.user.can_view_all_reports else None
    forms = FormTemplate.objects.filter(is_active=True).order_by('name')
    from accounts.models import Department
    departments = Department.objects.select_related('parent').order_by('order', 'name') if request.user.is_admin else None

    return render(request, 'dashboard/reports.html', {
        'submissions': submissions[:100],
        'total': total, 'flagged': flagged, 'perfect': perfect,
        'flagged_items': flagged_items[:200],
        'staff_list': staff_list, 'forms': forms, 'departments': departments,
        'f_staff':     params.get('staff', ''),
        'f_form':      params.get('form', ''),
        'f_dept':      params.get('dept', ''),
        'f_date_from': params.get('date_from', ''),
        'f_date_to':   params.get('date_to', ''),
        'f_response':  params.get('response', ''),
        'f_branch':    params.get('branch', ''),
    })


@login_required
def delete_submission(request, pk):
    if not request.user.can_delete_submissions:
        messages.error(request, 'You do not have permission to delete submissions.')
        return redirect('dashboard:reports')
    submission = get_object_or_404(FormSubmission, pk=pk)
    if request.method == 'POST':
        form_name = submission.form.name
        submission.delete()
        messages.success(request, f'Submission of "{form_name}" deleted.')
        return redirect('dashboard:reports')
    return render(request, 'dashboard/confirm_delete.html', {'submission': submission})


# ── Excel Export ────────────────────────────────────────────────────

@login_required
def export_excel(request):
    if not request.user.can_view_reports:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        messages.error(request, 'openpyxl is required. Run: pip install openpyxl')
        return redirect('dashboard:reports')

    from django.http import HttpResponse

    submissions = FormSubmission.objects.filter(status='submitted').select_related('form', 'submitted_by')
    submissions = _apply_filters(submissions, request, request.GET).order_by('-submitted_at')

    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')
    branch    = request.GET.get('branch', '')
    response_filter = request.GET.get('response', '')

    # Flagged items for second sheet
    flagged_items = ItemResponse.objects.filter(
        value__iexact='no', submission__in=submissions
    ).select_related('submission__submitted_by', 'submission__form', 'item__section').order_by('-submission__submitted_at')

    wb = openpyxl.Workbook()

    # ── Styles ──────────────────────────────────────
    header_font  = Font(bold=True, color='FFFFFF', size=11)
    header_fill  = PatternFill('solid', fgColor='1E3A5F')
    alt_fill     = PatternFill('solid', fgColor='F0F4F8')
    flag_fill    = PatternFill('solid', fgColor='FFF0F0')
    center       = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left         = Alignment(horizontal='left',   vertical='center', wrap_text=True)
    thin_border  = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0'),
    )

    def style_header_row(ws, cols):
        for col_idx, (header, width) in enumerate(cols, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center
            cell.border = thin_border
            ws.column_dimensions[get_column_letter(col_idx)].width = width
        ws.row_dimensions[1].height = 22

    def style_data_cell(cell, row_idx, is_flag=False):
        cell.alignment = left
        cell.border = thin_border
        if is_flag:
            cell.fill = flag_fill
        elif row_idx % 2 == 0:
            cell.fill = alt_fill

    # ── Sheet 1: Submissions ─────────────────────────
    ws1 = wb.active
    ws1.title = 'Submissions'
    ws1.freeze_panes = 'A2'

    cols1 = [
        ('Form',          28),
        ('Submitted By',  20),
        ('Branch',        14),
        ('Shift',         12),
        ('Date',          18),
        ('Time',          10),
        ('Completion %',  14),
        ('Issues (No)',   12),
        ('Status',        12),
    ]
    style_header_row(ws1, cols1)

    for row_idx, sub in enumerate(submissions, 2):
        is_flag = sub.no_responses > 0
        data = [
            sub.form.name,
            sub.submitted_by.display_name,
            sub.branch,
            sub.get_shift_display(),
            sub.submitted_at.strftime('%d %b %Y') if sub.submitted_at else '',
            sub.submitted_at.strftime('%H:%M')     if sub.submitted_at else '',
            sub.completion_percentage,
            sub.no_responses,
            'Issues Found' if is_flag else 'Clean',
        ]
        for col_idx, value in enumerate(data, 1):
            cell = ws1.cell(row=row_idx, column=col_idx, value=value)
            style_data_cell(cell, row_idx, is_flag)
            if col_idx in (7, 8):
                cell.alignment = Alignment(horizontal='center', vertical='center')

    ws1.auto_filter.ref = f'A1:{get_column_letter(len(cols1))}1'

    # ── Sheet 2: Flagged Items ───────────────────────
    ws2 = wb.create_sheet('Flagged Items')
    ws2.freeze_panes = 'A2'

    cols2 = [
        ('Checklist Item', 36),
        ('Section',        22),
        ('Form',           24),
        ('Submitted By',   20),
        ('Branch',         14),
        ('Date',           16),
        ('Comment / Explanation', 40),
        ('Photo Attached', 14),
    ]
    style_header_row(ws2, cols2)

    for row_idx, r in enumerate(flagged_items, 2):
        data = [
            r.item.label,
            r.item.section.title,
            r.submission.form.name,
            r.submission.submitted_by.display_name,
            r.submission.branch,
            r.submission.submitted_at.strftime('%d %b %Y') if r.submission.submitted_at else '',
            r.comment or '',
            'Yes' if r.image else 'No',
        ]
        for col_idx, value in enumerate(data, 1):
            cell = ws2.cell(row=row_idx, column=col_idx, value=value)
            cell.fill = flag_fill
            cell.alignment = left
            cell.border = thin_border

    ws2.auto_filter.ref = f'A1:{get_column_letter(len(cols2))}1'

    # ── Sheet 3: Summary ─────────────────────────────
    ws3 = wb.create_sheet('Summary')
    summary_data = [
        ('Report Generated',  timezone.now().strftime('%d %b %Y %H:%M')),
        ('Generated By',      request.user.display_name),
        ('Total Submissions', submissions.count()),
        ('Clean (No Issues)', submissions.filter(no_responses=0).count()),
        ('With Issues',       submissions.filter(no_responses__gt=0).count()),
        ('Total Flagged Items', flagged_items.count()),
        ('Filters Applied', ''),
        ('  Date From',  date_from  or 'All dates'),
        ('  Date To',    date_to    or 'All dates'),
        ('  Branch',     branch     or 'All branches'),
        ('  Response',   response_filter or 'All'),
    ]
    ws3.column_dimensions['A'].width = 24
    ws3.column_dimensions['B'].width = 30
    for row_idx, (label, value) in enumerate(summary_data, 1):
        a = ws3.cell(row=row_idx, column=1, value=label)
        b = ws3.cell(row=row_idx, column=2, value=value)
        a.font = Font(bold=True, color='1E3A5F')
        a.alignment = left
        b.alignment = left
        if row_idx <= 6:
            a.fill = PatternFill('solid', fgColor='E8F4FD')
            b.fill = PatternFill('solid', fgColor='E8F4FD')

    # ── Return file ──────────────────────────────────
    from io import BytesIO
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"SystemX_Report_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ── Print Report ─────────────────────────────────────────────────

@login_required
def print_report(request):
    if not request.user.can_view_reports:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')

    submissions = FormSubmission.objects.filter(status='submitted').select_related('form', 'submitted_by')
    submissions = _apply_filters(submissions, request, request.GET).order_by('-submitted_at')

    flagged_items = ItemResponse.objects.filter(
        value__iexact='no', submission__in=submissions
    ).select_related('submission__submitted_by', 'submission__form', 'item__section')

    total   = submissions.count()
    flagged = submissions.filter(no_responses__gt=0).count()
    perfect = submissions.filter(no_responses=0).count()

    return render(request, 'dashboard/print_report.html', {
        'submissions': submissions,
        'flagged_items': flagged_items,
        'total': total, 'flagged': flagged, 'perfect': perfect,
        'date_from': request.GET.get('date_from', ''),
        'date_to':   request.GET.get('date_to', ''),
        'generated_by': request.user.display_name,
        'generated_at': timezone.now(),
    })
