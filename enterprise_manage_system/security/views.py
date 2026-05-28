from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from hr.models import Employee
from finance.models import BankAccount
from .permissions import check_role, ROLE_ADMIN, ROLE_HR_MANAGER, ROLE_ACCOUNTANT, ROLE_EMPLOYEE
from .queryset_filters import filter_employee_queryset_by_user, filter_salary_queryset_by_user
from security.middleware import log_access_denied


class EmployeeAccessMixin:

    def get_queryset(self):
        queryset = super().get_queryset()
        return filter_employee_queryset_by_user(queryset, self.request.user)

    def get_object(self):
        obj = super().get_object()

        if hasattr(self, 'check_salary_access') and self.check_salary_access:
            if not check_role(self.request.user, [ROLE_ADMIN, ROLE_ACCOUNTANT, ROLE_HR_MANAGER]):
                if obj != getattr(self.request.user, 'employee', None):
                    log_access_denied(self.request, f"Попытка просмотра зарплаты сотрудника {obj.name}")
                    raise PermissionDenied("Доступ к зарплатам других сотрудников запрещён")

        return obj


@login_required
def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)

    allowed_employees = filter_employee_queryset_by_user(Employee.objects.all(), request.user)

    if employee not in allowed_employees:
        log_access_denied(request, f"Попытка просмотра сотрудника {employee.name}")
        raise PermissionDenied("Доступ к карточке сотрудника запрещён")

    can_view_salary = check_role(request.user, [ROLE_ADMIN, ROLE_ACCOUNTANT, ROLE_HR_MANAGER])

    context = {
        'employee': employee,
        'can_view_salary': can_view_salary,
        'salary': employee.position.base_salary if can_view_salary else None,
    }

    return context


@login_required
def employee_balance(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)

    if request.user.is_superuser:
        pass
    elif hasattr(request.user, 'employee') and request.user.employee == employee:
        pass
    elif check_role(request.user, [ROLE_ADMIN, ROLE_ACCOUNTANT]):
        pass
    else:
        log_access_denied(request, f"Попытка просмотра баланса сотрудника {employee.name}")
        raise PermissionDenied("Доступ к балансу запрещён")

    try:
        bank_account = BankAccount.objects.get(employee=employee)
        balance = bank_account.balance
    except BankAccount.DoesNotExist:
        balance = 0

    return {'employee': employee, 'balance': balance}
