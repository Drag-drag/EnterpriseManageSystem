from celery import Celery
from decimal import Decimal
from django.db import transaction as db_transaction


def run_payday_task():
    from finance.services import PaymentService
    from hr.models import Employee

    print("[CELERY] Задача выплаты зарплаты запущена")

    payment_service = PaymentService()
    employees = Employee.objects.all()

    results = []
    for employee in employees:
        with db_transaction.atomic():
            result = payment_service.process_payroll(
                employee=employee,
                transaction_type='salary',
                description='Ежемесячное начисление зарплаты'
            )
            results.append({
                'employee': employee.name,
                'success': result.get('success', False),
                'amount': float(result.get('total_amount', 0)) if result.get('success') else 0,
                'error': result.get('error') if not result.get('success') else None
            })

    print(f"[CELERY] Выплачено сотрудников: {sum(1 for r in results if r['success'])}")
    return results


def run_tax_transfer_task():
    from reports.services import ReportGenerator

    print("[CELERY] Задача перевода налогов запущена")

    report_gen = ReportGenerator()
    tax_data = report_gen.generate_tax_report()

    print(f"[CELERY] Сумма налогов к уплате: {tax_data['total_ndfl']} ₽")

    return tax_data


def run_vacation_check_task():
    from hr.models import Employee
    from datetime import date

    print("[CELERY] Задача проверки отпусков запущена")

    result = {
        'can_take_vacation': [],
        'cannot_take_vacation': []
    }

    for employee in Employee.objects.all():
        if employee.age < 60:
            result['can_take_vacation'].append(employee.name)
        else:
            result['cannot_take_vacation'].append(employee.name)

    return result
