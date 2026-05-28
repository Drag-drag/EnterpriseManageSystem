from datetime import datetime
from decimal import Decimal
from django.template.loader import render_to_string
from hr.models import Employee, Employment
from finance.models import BankAccount


class DocumentGenerator:

    def generate_contract(self, employee_id):
        try:
            employee = Employee.objects.get(pk=employee_id)
            employments = employee.employments.filter(job_type='main').first()

            context = {
                'contract_number': f"TD-{employee.id}-{datetime.now().year}",
                'city': 'Москва',
                'date': datetime.now().strftime('%d.%m.%Y'),
                'enterprise_name': employee.position.enterprise.name,
                'enterprise_inn': employee.position.enterprise.inn,
                'enterprise_ogrn': employee.position.enterprise.ogrn,
                'enterprise_address': employee.position.enterprise.address,
                'employee_name': employee.name,
                'position': employee.position.title,
                'base_salary': float(employee.position.base_salary),
                'start_date': datetime.now().strftime('%d.%m.%Y'),
                'end_date': None,
            }

            if employments and employments.department:
                context['department'] = employments.department.name

            # Рендеринг HTML-шаблона
            document_html = render_to_string('documents/contract_template.html', context)

            return {
                'success': True,
                'document': document_html,
                'document_type': 'contract',
                'employee_id': employee_id,
                'context': context
            }

        except Employee.DoesNotExist:
            return {'success': False, 'error': 'Сотрудник не найден'}

    def generate_tax_form_2ndfl(self, employee_id, year):
        try:
            employee = Employee.objects.get(pk=employee_id)

            # Расчёт дохода по месяцам (упрощённо)
            monthly_salary = Decimal('0.00')
            employments = employee.employments.filter(job_type='main')

            for employment in employments:
                monthly_salary += employment.calculate_salary()

            total_income = monthly_salary * 12
            tax_rate = 13
            tax_amount = total_income * Decimal(str(tax_rate)) / Decimal('100')
            taxable_income = total_income

            months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

            monthly_income = []
            for month in months:
                monthly_income.append({
                    'name': month,
                    'amount': float(monthly_salary),
                    'deduction': 1400 if month in ['Январь', 'Февраль'] else 0  # пример вычета
                })

            context = {
                'year': year,
                'employee_name': employee.name,
                'employee_inn': getattr(employee, 'inn', '__________'),
                'employee_birth_date': getattr(employee, 'birth_date', '__________'),
                'enterprise_name': employee.position.enterprise.name,
                'enterprise_inn': employee.position.enterprise.inn,
                'enterprise_kpp': getattr(employee.position.enterprise, 'kpp', '__________'),
                'monthly_income': monthly_income,
                'total_income': float(total_income),
                'total_deduction': 2800,  # пример
                'taxable_income': float(taxable_income),
                'tax_rate': tax_rate,
                'tax_amount': float(tax_amount),
                'generation_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            }

            document_html = render_to_string('documents/tax_form_2ndfl.html', context)

            return {
                'success': True,
                'document': document_html,
                'document_type': '2-NDFL',
                'employee_id': employee_id,
                'year': year,
                'context': context,
                'data': {
                    'total_income': float(total_income),
                    'tax_amount': float(tax_amount)
                }
            }

        except Employee.DoesNotExist:
            return {'success': False, 'error': 'Сотрудник не найден'}

    def generate_payslip(self, employee_id, month=None):
        try:
            employee = Employee.objects.get(pk=employee_id)

            if not month:
                month = datetime.now().strftime('%Y-%m')

            employments = employee.employments.all()
            payroll_details = []
            total = Decimal('0.00')

            for employment in employments:
                salary = employment.calculate_salary()
                total += salary
                payroll_details.append({
                    'type': employment.get_job_type_display(),
                    'type_code': employment.job_type,
                    'rate': float(employment.rate),
                    'salary': float(salary),
                })

            context = {
                'month': month,
                'employee_name': employee.name,
                'position': employee.position.title,
                'department': employments.filter(job_type='main').first().department.name if employments.filter(
                    job_type='main').first() and employments.filter(job_type='main').first().department else None,
                'payroll_details': payroll_details,
                'total': float(total),
                'generation_date': datetime.now().strftime('%d.%m.%Y'),
            }

            document_html = render_to_string('documents/payslip_template.html', context)

            return {
                'success': True,
                'document': document_html,
                'document_type': 'payslip',
                'employee_id': employee_id,
                'month': month,
                'total': float(total)
            }

        except Employee.DoesNotExist:
            return {'success': False, 'error': 'Сотрудник не найден'}
