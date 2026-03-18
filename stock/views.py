from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal
from .models import (
    StockCategory, StockItem, StockLocation,
    StockCount, StockCountLine, StockMovement
)


def stock_required(fn):
    """Access controlled by role permission can_access_stock."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.can_access_stock:
            messages.error(request, 'You do not have permission to access Stock Management.')
            return redirect('dashboard:home')
        return fn(request, *args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


def stock_manage_required(fn):
    """Only users with can_manage_stock can add/edit items, categories, locations."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.can_manage_stock:
            messages.error(request, 'You do not have permission to manage stock items.')
            return redirect('stock:dashboard')
        return fn(request, *args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


# ── Dashboard ──────────────────────────────────────────────────────

@login_required
@stock_required
def stock_dashboard(request):
    items = StockItem.objects.filter(is_active=True).select_related('category', 'location')

    total_items     = items.count()
    out_of_stock    = [i for i in items if i.stock_status == 'out']
    critical        = [i for i in items if i.stock_status == 'critical']
    below_par       = [i for i in items if i.stock_status == 'low']
    ok_items        = [i for i in items if i.stock_status == 'ok']

    # Total stock value
    total_value = sum(i.current_stock * i.unit_cost for i in items)

    # Items needing order
    needs_order = [i for i in items if i.order_qty_needed > 0]

    # Recent movements
    recent_movements = StockMovement.objects.select_related('item', 'created_by').order_by('-created_at')[:10]

    # Recent counts
    recent_counts = StockCount.objects.select_related('location', 'conducted_by').order_by('-count_date')[:5]

    # Category breakdown
    categories = StockCategory.objects.filter(is_active=True)

    return render(request, 'stock/dashboard.html', {
        'total_items':      total_items,
        'out_of_stock':     out_of_stock,
        'critical':         critical,
        'below_par':        below_par,
        'ok_items':         ok_items,
        'total_value':      total_value,
        'needs_order':      needs_order,
        'recent_movements': recent_movements,
        'recent_counts':    recent_counts,
        'categories':       categories,
    })


# ── Stock Items ────────────────────────────────────────────────────

@login_required
@stock_required
def item_list(request):
    status_filter   = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    location_filter = request.GET.get('location', '')
    search          = request.GET.get('q', '').strip()

    items = StockItem.objects.filter(is_active=True).select_related('category', 'location')

    if search:
        items = items.filter(Q(name__icontains=search) | Q(sku__icontains=search))
    if category_filter:
        items = items.filter(category_id=category_filter)
    if location_filter:
        items = items.filter(location_id=location_filter)

    items = list(items)
    if status_filter == 'out':
        items = [i for i in items if i.stock_status == 'out']
    elif status_filter == 'critical':
        items = [i for i in items if i.stock_status == 'critical']
    elif status_filter == 'low':
        items = [i for i in items if i.stock_status == 'low']
    elif status_filter == 'order':
        items = [i for i in items if i.order_qty_needed > 0]

    categories = StockCategory.objects.filter(is_active=True)
    locations  = StockLocation.objects.filter(is_active=True)

    return render(request, 'stock/item_list.html', {
        'items': items, 'categories': categories, 'locations': locations,
        'f_status': status_filter, 'f_category': category_filter,
        'f_location': location_filter, 'f_q': search,
    })


@login_required
@stock_required
def item_detail(request, pk):
    item = get_object_or_404(StockItem, pk=pk)
    movements = item.movements.select_related('created_by').order_by('-created_at')[:30]
    count_lines = item.count_lines.select_related('count__location').order_by('-count__count_date')[:10]
    return render(request, 'stock/item_detail.html', {
        'item': item, 'movements': movements, 'count_lines': count_lines
    })


@login_required
@stock_manage_required
def item_create(request):
    from .forms import StockItemForm
    if request.method == 'POST':
        form = StockItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stock item created.')
            return redirect('stock:item_list')
    else:
        form = StockItemForm()
    return render(request, 'stock/item_form.html', {'form': form, 'title': 'Add Stock Item'})


@login_required
@stock_manage_required
def item_edit(request, pk):
    from .forms import StockItemForm
    item = get_object_or_404(StockItem, pk=pk)
    if request.method == 'POST':
        form = StockItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{item.name}" updated.')
            return redirect('stock:item_list')
    else:
        form = StockItemForm(instance=item)
    return render(request, 'stock/item_form.html', {'form': form, 'title': f'Edit: {item.name}', 'item': item})


# ── Stock Counts ───────────────────────────────────────────────────

@login_required
@stock_required
def count_list(request):
    counts = StockCount.objects.select_related('location', 'conducted_by').order_by('-count_date', '-created_at')
    return render(request, 'stock/count_list.html', {'counts': counts})


@login_required
@stock_required
def count_create(request):
    from .forms import StockCountForm
    if request.method == 'POST':
        form = StockCountForm(request.POST)
        if form.is_valid():
            count = form.save(commit=False)
            count.conducted_by = request.user
            count.save()
            # Pre-populate lines with all items for this location
            location = count.location
            items = StockItem.objects.filter(is_active=True)
            if location:
                items = items.filter(Q(location=location) | Q(location__isnull=True))
            for item in items:
                StockCountLine.objects.create(
                    count=count,
                    item=item,
                    expected_qty=item.current_stock,
                )
            messages.success(request, f'Stock count started for {location}.')
            return redirect('stock:count_fill', pk=count.pk)
    else:
        form = StockCountForm()
    return render(request, 'stock/count_form.html', {'form': form, 'title': 'Start Stock Count'})


@login_required
@stock_required
def count_fill(request, pk):
    count = get_object_or_404(StockCount, pk=pk)
    if count.status == StockCount.STATUS_COMPLETED:
        messages.info(request, 'This count is already completed.')
        return redirect('stock:count_detail', pk=count.pk)

    lines = count.lines.select_related('item__category', 'item__location').order_by(
        'item__category__name', 'item__name'
    )
    # Group by category
    from itertools import groupby
    grouped = {}
    for line in lines:
        cat = line.item.category.name
        grouped.setdefault(cat, []).append(line)

    return render(request, 'stock/count_fill.html', {
        'count': count, 'grouped': grouped, 'lines': lines,
    })


@login_required
@stock_required
def save_count_line(request, count_pk):
    """AJAX: save a single count line qty."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    count = get_object_or_404(StockCount, pk=count_pk)
    if count.status == StockCount.STATUS_COMPLETED:
        return JsonResponse({'error': 'Count already completed'}, status=400)

    line_id = request.POST.get('line_id')
    qty_str = request.POST.get('qty', '').strip()

    try:
        line = StockCountLine.objects.get(pk=line_id, count=count)
        if qty_str == '':
            line.counted_qty = None
            line.variance = None
        else:
            line.counted_qty = Decimal(qty_str)
            line.variance = line.counted_qty - line.expected_qty
        line.save()
        return JsonResponse({
            'ok': True,
            'variance': float(line.variance) if line.variance is not None else None,
            'variance_status': line.variance_status,
            'below_par': line.below_par,
            'completion': count.completion_pct,
        })
    except (StockCountLine.DoesNotExist, Exception) as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@stock_required
def count_complete(request, pk):
    count = get_object_or_404(StockCount, pk=pk)
    if request.method == 'POST':
        count.complete()
        messages.success(request, f'Stock count completed. {count.total_items} items updated.')
        return redirect('stock:count_detail', pk=count.pk)
    return render(request, 'stock/count_confirm_complete.html', {'count': count})


@login_required
@stock_required
def count_detail(request, pk):
    count = get_object_or_404(StockCount, pk=pk)
    lines = count.lines.select_related('item__category').order_by('item__category__name', 'item__name')
    grouped = {}
    for line in lines:
        cat = line.item.category.name
        grouped.setdefault(cat, []).append(line)
    return render(request, 'stock/count_detail.html', {'count': count, 'grouped': grouped})


# ── Stock Movements ────────────────────────────────────────────────

@login_required
@stock_required
def movement_list(request):
    movements = StockMovement.objects.select_related('item', 'created_by').order_by('-created_at')[:100]
    return render(request, 'stock/movement_list.html', {'movements': movements})


@login_required
@stock_required
def movement_create(request, item_pk=None):
    from .forms import StockMovementForm
    initial = {}
    if item_pk:
        item = get_object_or_404(StockItem, pk=item_pk)
        initial['item'] = item
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.created_by = request.user
            movement.save()
            messages.success(request, f'Movement recorded: {movement}')
            return redirect('stock:item_detail', pk=movement.item.pk)
    else:
        form = StockMovementForm(initial=initial)
    return render(request, 'stock/movement_form.html', {'form': form, 'title': 'Record Stock Movement'})


# ── PAR Level Report ───────────────────────────────────────────────

@login_required
@stock_required
def par_report(request):
    items = StockItem.objects.filter(is_active=True).select_related('category', 'location').order_by(
        'category__name', 'name'
    )
    category_filter = request.GET.get('category', '')
    if category_filter:
        items = items.filter(category_id=category_filter)

    categories = StockCategory.objects.filter(is_active=True)

    # Build order list with pre-calculated cost
    order_list = []
    for i in items:
        if i.order_qty_needed > 0:
            est_cost = float(i.order_qty_needed) * float(i.unit_cost)
            order_list.append({
                'item': i,
                'order_qty': i.order_qty_needed,
                'unit_cost': i.unit_cost,
                'est_cost': round(est_cost, 2),
            })
    total_order_value = sum(o['est_cost'] for o in order_list)

    return render(request, 'stock/par_report.html', {
        'items': items,
        'order_list': order_list,
        'total_order_value': total_order_value,
        'categories': categories,
        'f_category': category_filter,
    })


# ── Categories ────────────────────────────────────────────────────

@login_required
@stock_manage_required
def category_list(request):
    cats = StockCategory.objects.annotate(item_count=Count('items')).order_by('name')
    return render(request, 'stock/category_list.html', {'cats': cats})


@login_required
@stock_manage_required
def category_create(request):
    from .forms import StockCategoryForm
    if request.method == 'POST':
        form = StockCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created.')
            return redirect('stock:category_list')
    else:
        form = StockCategoryForm()
    return render(request, 'stock/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required
@stock_manage_required
def category_edit(request, pk):
    from .forms import StockCategoryForm
    cat = get_object_or_404(StockCategory, pk=pk)
    if request.method == 'POST':
        form = StockCategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{cat.name}" updated.')
            return redirect('stock:category_list')
    else:
        form = StockCategoryForm(instance=cat)
    return render(request, 'stock/category_form.html', {'form': form, 'title': f'Edit: {cat.name}', 'cat': cat})


@login_required
@stock_manage_required
def category_delete(request, pk):
    cat = get_object_or_404(StockCategory, pk=pk)
    if request.method == 'POST':
        if cat.items.exists():
            messages.error(request, f'Cannot delete "{cat.name}" — {cat.items.count()} item(s) use this category. Reassign them first.')
            return redirect('stock:category_list')
        cat.delete()
        messages.success(request, f'Category "{cat.name}" deleted.')
        return redirect('stock:category_list')
    return render(request, 'stock/confirm_delete.html', {
        'title': f'Delete Category: {cat.name}',
        'message': f'This will permanently delete the "{cat.name}" category. Make sure no items are using it.',
        'back_url': 'stock:category_list',
    })


# ── Locations ─────────────────────────────────────────────────────

@login_required
@stock_manage_required
def location_list(request):
    locs = StockLocation.objects.select_related('department').annotate(item_count=Count('items')).order_by('name')
    return render(request, 'stock/location_list.html', {'locs': locs})


@login_required
@stock_manage_required
def location_create(request):
    from .forms import StockLocationForm
    if request.method == 'POST':
        form = StockLocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Location created.')
            return redirect('stock:location_list')
    else:
        form = StockLocationForm()
    return render(request, 'stock/location_form.html', {'form': form, 'title': 'Add Location'})


@login_required
@stock_manage_required
def location_edit(request, pk):
    from .forms import StockLocationForm
    loc = get_object_or_404(StockLocation, pk=pk)
    if request.method == 'POST':
        form = StockLocationForm(request.POST, instance=loc)
        if form.is_valid():
            form.save()
            messages.success(request, f'Location "{loc.name}" updated.')
            return redirect('stock:location_list')
    else:
        form = StockLocationForm(instance=loc)
    return render(request, 'stock/location_form.html', {'form': form, 'title': f'Edit: {loc.name}', 'loc': loc})


@login_required
@stock_manage_required
def location_delete(request, pk):
    loc = get_object_or_404(StockLocation, pk=pk)
    if request.method == 'POST':
        if loc.items.exists():
            messages.error(request, f'Cannot delete "{loc.name}" — {loc.items.count()} item(s) stored here. Reassign them first.')
            return redirect('stock:location_list')
        loc.delete()
        messages.success(request, f'Location "{loc.name}" deleted.')
        return redirect('stock:location_list')
    return render(request, 'stock/confirm_delete.html', {
        'title': f'Delete Location: {loc.name}',
        'message': f'This will permanently delete the "{loc.name}" location.',
        'back_url': 'stock:location_list',
    })
