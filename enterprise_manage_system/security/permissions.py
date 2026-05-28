from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group, User
from functools import wraps

ROLE_ADMIN = 'Admin'
ROLE_HR_MANAGER = 'HR_Manager'
ROLE_ACCOUNTANT = 'Accountant'
ROLE_EMPLOYEE = 'Employee'
ROLE_AUDITOR = 'Auditor'

ROLES = {
    ROLE_ADMIN: ['can_view_all_employees', 'can_edit_all_employees', 'can_view_salaries', 'can_edit_salaries',
                 'can_view_audit_log'],
    ROLE_HR_MANAGER: ['can_view_all_employees', 'can_edit_all_employees', 'can_view_salaries'],
    ROLE_ACCOUNTANT: ['can_view_all_employees', 'can_view_salaries', 'can_edit_salaries'],
    ROLE_EMPLOYEE: ['can_view_own_profile', 'can_view_own_balance'],
    ROLE_AUDITOR: ['can_view_audit_log', 'can_view_all_employees'],
}


def check_role(user, required_roles):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    user_roles = user.groups.values_list('name', flat=True)
    return any(role in user_roles for role in required_roles)


def role_required(required_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not check_role(request.user, required_roles):
                raise PermissionDenied("Доступ запрещён. Требуемая роль: " + ", ".join(required_roles))
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_user_role(user):
    if user.is_superuser:
        return ROLE_ADMIN
    groups = user.groups.all()
    if groups.exists():
        return groups.first().name
    return None


def setup_groups():
    for role_name, permissions in ROLES.items():
        group, created = Group.objects.get_or_create(name=role_name)
        if created:
            from django.contrib.auth.models import Permission
            for perm_codename in permissions:
                try:
                    permission = Permission.objects.get(codename=perm_codename)
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    pass