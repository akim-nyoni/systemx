from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .models import User, Role
from .forms import LoginForm, UserCreateForm, UserEditForm, ProfileEditForm, RoleForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
        if user and user.is_active:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard:home'))
        else:
            messages.error(request, 'Invalid credentials or account disabled.')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """Users can edit their own profile but NOT username or role."""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


# ── User Management (requires can_manage_users) ────────────────────

def _require_user_mgmt(request):
    if not request.user.can_manage_users:
        messages.error(request, 'Access denied. You do not have user management permissions.')
        return False
    return True


@login_required
def user_list_view(request):
    if not _require_user_mgmt(request):
        return redirect('dashboard:home')
    users = User.objects.select_related('custom_role').order_by('first_name', 'username')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
def user_create_view(request):
    if not _require_user_mgmt(request):
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully.')
            return redirect('accounts:user_list')
    else:
        form = UserCreateForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Create User'})


@login_required
def user_edit_view(request, pk):
    if not _require_user_mgmt(request):
        return redirect('dashboard:home')
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'{user.display_name} updated successfully.')
            return redirect('accounts:user_list')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'title': f'Edit {user.display_name}', 'edit_user': user})


@login_required
def user_toggle_active_view(request, pk):
    if not _require_user_mgmt(request):
        return redirect('dashboard:home')
    user = get_object_or_404(User, pk=pk)
    if user != request.user:
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'{user.display_name} has been {status}.')
    else:
        messages.warning(request, 'You cannot deactivate your own account.')
    return redirect('accounts:user_list')


@login_required
def user_delete_view(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Only administrators can delete users.')
        return redirect('dashboard:home')
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('accounts:user_list')
    if request.method == 'POST':
        name = user.display_name
        user.delete()
        messages.success(request, f'User "{name}" deleted.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'edit_user': user})


# ── Role Management (admin only) ──────────────────────────────────

@login_required
def role_list_view(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    roles = Role.objects.annotate(user_count=__import__('django.db.models', fromlist=['Count']).Count('users')).order_by('name')
    return render(request, 'accounts/role_list.html', {'roles': roles})


@login_required
def role_create_view(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role created successfully.')
            return redirect('accounts:role_list')
    else:
        form = RoleForm()
    return render(request, 'accounts/role_form.html', {'form': form, 'title': 'Create Role'})


@login_required
def role_edit_view(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    role = get_object_or_404(Role, pk=pk)
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, f'Role "{role.name}" updated.')
            return redirect('accounts:role_list')
    else:
        form = RoleForm(instance=role)
    return render(request, 'accounts/role_form.html', {'form': form, 'title': f'Edit Role: {role.name}', 'role': role})


@login_required
def role_delete_view(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    role = get_object_or_404(Role, pk=pk)
    if request.method == 'POST':
        if role.users.exists():
            messages.error(request, f'Cannot delete "{role.name}" — {role.users.count()} user(s) still assigned to it.')
            return redirect('accounts:role_list')
        role.delete()
        messages.success(request, f'Role "{role.name}" deleted.')
        return redirect('accounts:role_list')
    return render(request, 'accounts/role_confirm_delete.html', {'role': role})


# ── Department Management (admin only) ───────────────────────────

@login_required
def dept_list_view(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    from .forms import DepartmentForm
    from .models import Department
    from django.db.models import Count
    depts = Department.objects.annotate(
        user_count=Count('users')
    ).select_related('parent', 'outlet').prefetch_related('children').order_by('outlet__order', 'order', 'name')
    return render(request, 'accounts/dept_list.html', {'depts': depts})


@login_required
def dept_create_view(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    from .forms import DepartmentForm
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department created.')
            return redirect('accounts:dept_list')
    else:
        form = DepartmentForm()
    return render(request, 'accounts/dept_form.html', {'form': form, 'title': 'Create Department'})


@login_required
def dept_edit_view(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    from .forms import DepartmentForm
    from .models import Department
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, f'Department "{dept.name}" updated.')
            return redirect('accounts:dept_list')
    else:
        form = DepartmentForm(instance=dept)
    return render(request, 'accounts/dept_form.html', {'form': form, 'title': f'Edit: {dept.name}', 'dept': dept})


@login_required
def dept_delete_view(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    from .models import Department
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        if dept.users.exists():
            messages.error(request, f'Cannot delete "{dept.name}" — {dept.users.count()} user(s) still assigned.')
            return redirect('accounts:dept_list')
        dept.delete()
        messages.success(request, f'Department "{dept.name}" deleted.')
        return redirect('accounts:dept_list')
    return render(request, 'accounts/dept_confirm_delete.html', {'dept': dept})


# ── Outlet Management (admin only) ───────────────────────────────

@login_required
def outlet_list_view(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    from .models import Outlet
    from django.db.models import Count
    outlets = Outlet.objects.annotate(user_count=Count('users')).order_by('order')
    return render(request, 'accounts/outlet_list.html', {'outlets': outlets})


@login_required
def outlet_create_view(request):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    from .forms import OutletForm
    if request.method == 'POST':
        form = OutletForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Outlet created.')
            return redirect('accounts:outlet_list')
    else:
        form = OutletForm()
    return render(request, 'accounts/outlet_form.html', {'form': form, 'title': 'Add Outlet'})


@login_required
def outlet_edit_view(request, pk):
    if not request.user.is_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    from .models import Outlet
    from .forms import OutletForm
    outlet = get_object_or_404(Outlet, pk=pk)
    if request.method == 'POST':
        form = OutletForm(request.POST, instance=outlet)
        if form.is_valid():
            form.save()
            messages.success(request, f'Outlet "{outlet.name}" updated.')
            return redirect('accounts:outlet_list')
    else:
        form = OutletForm(instance=outlet)
    return render(request, 'accounts/outlet_form.html', {'form': form, 'title': f'Edit: {outlet.name}', 'outlet': outlet})


# ── Admin: Reset any user's password ─────────────────────────────

@login_required
def reset_user_password_view(request, pk):
    """Admin resets another user's password. No old password required."""
    if not request.user.can_manage_users:
        messages.error(request, 'You do not have permission to reset passwords.')
        return redirect('accounts:user_list')

    target_user = get_object_or_404(User, pk=pk)

    # Prevent non-admins from resetting admin passwords
    if target_user.is_admin and not request.user.is_admin:
        messages.error(request, 'You cannot reset an administrator\'s password.')
        return redirect('accounts:user_list')

    if request.method == 'POST':
        new_password  = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not new_password:
            messages.error(request, 'Password cannot be empty.')
        elif len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
        elif new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        else:
            target_user.set_password(new_password)
            target_user.save()
            messages.success(
                request,
                f'Password for {target_user.display_name} has been reset successfully.'
            )
            return redirect('accounts:user_list')

    return render(request, 'accounts/reset_password.html', {
        'target_user': target_user,
    })
