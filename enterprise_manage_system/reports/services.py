from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime
from hr.models import Enterprise, Department, Employee, Employment
from finance.models import BankAccount, Transaction


class ReportGenerator:

    def generate_payroll_report(self, department_id=None, month=None):
        if month:
            try:
                report_month = datetime.strptime(month, "%Y-%m")
            except ValueError:
                report_month = timezone.now()
        else:
            report_month = timezone.now()


        employments = Employment.objects.filter(
            job_type='main'
        )

        if department_id:
            employments = employments.filter(department_id=department_id)

        total_fund = Decimal('0.00')
        payroll_details = []

        for employment in employments:
            salary = employment.calculate_salary()
            total_fund += salary

            payroll_details.append({
                'employee_name': employment.employee.name,
                'position': employment.employee.position.title,
                'department': employment.department.name if employment.department else None,
                'salary': float(salary),
                'rate': float(employment.rate),
            })

        return {
            'total_fund': float(total_fund),
            'month': report_month.strftime("%Y-%m"),
            'employees_count': len(payroll_details),
            'details': payroll_details
        }

    def generate_tax_report(self, enterprise_id=None):
        employees = Employee.objects.all()

        if enterprise_id:
            employees = employees.filter(position__enterprise_id=enterprise_id)

        total_salary = Decimal('0.00')
        total_tax = Decimal('0.00')

        for employee in employees:
            employments = employee.employments.filter(job_type='main')
            for employment in employments:
                salary = employment.calculate_salary()
                total_salary += salary
                # НДФЛ 13%
                total_tax += salary * Decimal('0.13')

        return {
            'total_salary_fund': float(total_salary),
            'total_ndfl': float(total_tax),
            'tax_rate': 13,
            'employees_count': employees.count()
        }

    def generate_department_efficiency_report(self):
        departments = Department.objects.all()
        report = []

        for department in departments:
            employments = department.employments.filter(job_type='main')
            total_salary = Decimal('0.00')

            for employment in employments:
                total_salary += employment.calculate_salary()

            report.append({
                'department_name': department.name,
                'enterprise': department.enterprise.name,
                'employees_count': employments.count(),
                'total_salary_fund': float(total_salary),
                'average_salary': float(total_salary / employments.count()) if employments.count() > 0 else 0,
            })

        return sorted(report, key=lambda x: x['total_salary_fund'], reverse=True)

    def generate_financial_report(self):
        accounts = BankAccount.objects.filter(is_active=True)

        total_balance = accounts.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')

        return {
            'total_balance': float(total_balance),
            'active_accounts': accounts.count(),
            'accounts': [
                {
                    'employee': acc.employee.name,
                    'account_number': acc.account_number,
                    'balance': float(acc.balance),
                }
                for acc in accounts
            ]
        }