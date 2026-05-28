def filter_employee_queryset_by_user(queryset, user):
    if user.is_superuser:
        return queryset

    from .permissions import check_role, ROLE_ADMIN, ROLE_HR_MANAGER, ROLE_ACCOUNTANT, ROLE_AUDITOR

    if check_role(user, [ROLE_ADMIN, ROLE_HR_MANAGER, ROLE_ACCOUNTANT, ROLE_AUDITOR]):
        return queryset

    return queryset.filter(user=user) if hasattr(user, 'employee') else queryset.none()


def filter_salary_queryset_by_user(queryset, user):
    if user.is_superuser:
        return queryset

    from .permissions import check_role, ROLE_ADMIN, ROLE_ACCOUNTANT, ROLE_HR_MANAGER

    if check_role(user, [ROLE_ADMIN, ROLE_ACCOUNTANT, ROLE_HR_MANAGER]):
        return queryset

    return queryset.none()