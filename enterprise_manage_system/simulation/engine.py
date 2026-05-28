from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q, F
from django.core.cache import cache
from datetime import datetime, timedelta
from hr.models import Enterprise, Department, Position, Employee, Employment
from finance.models import BankAccount, Transaction
from reports.services import ReportGenerator


class BusinessSimulator:

    def __init__(self):
        self.report_gen = ReportGenerator()

    def simulate_mass_hiring(self, count, department_id=None, position_id=None):
        if position_id:
            position = Position.objects.get(pk=position_id)
            base_salary = position.base_salary
        elif department_id:
            department = Department.objects.get(pk=department_id)

            employments = Employment.objects.filter(department_id=department_id, job_type='main')
            avg_salary = employments.aggregate(avg=Avg('employee__position__base_salary'))['avg'] or Decimal('100000')
            base_salary = Decimal(str(avg_salary))
        else:
            base_salary = Decimal('80000')

        additional_payroll = base_salary * Decimal(str(count))
        tax_rate = Decimal('0.13')
        additional_tax = additional_payroll * tax_rate

        cache_key = f"hiring_sim_{count}_{department_id}_{position_id}"
        result = cache.get(cache_key)

        if not result:
            result = {
                'payroll_delta': float(additional_payroll),
                'tax_delta': float(additional_tax),
                'new_employees_count': count,
                'base_salary_used': float(base_salary),
                'monthly_payroll_increase': float(additional_payroll),
                'yearly_payroll_increase': float(additional_payroll * 12),
            }
            cache.set(cache_key, result, 3600)

        return result

    def simulate_crisis(self, reduction_percent):
        total_payroll = Decimal('0.00')
        total_bonuses = Decimal('0.00')

        payroll_data = self.report_gen.generate_payroll_report()
        total_payroll = Decimal(str(payroll_data['total_fund']))

        bonus_sum = Transaction.objects.filter(
            type='bonus',
            date__month=datetime.now().month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total_bonuses = Decimal(str(bonus_sum))

        reduction_amount = total_payroll * Decimal(str(reduction_percent)) / Decimal('100')

        total_employees = Employee.objects.count()
        max_layoffs = int(total_employees * 0.3)

        avg_salary = total_payroll / Decimal(str(total_employees)) if total_employees > 0 else Decimal('80000')
        required_layoffs = int(reduction_amount / avg_salary) if avg_salary > 0 else 0
        required_layoffs = min(required_layoffs, max_layoffs)

        min_bonus_level = Decimal('0.1')
        bonus_reduction = total_bonuses * (Decimal('1') - min_bonus_level)

        result = {
            'current_payroll': float(total_payroll),
            'current_bonuses': float(total_bonuses),
            'reduction_target': float(reduction_amount),
            'required_layoffs': required_layoffs,
            'max_possible_layoffs': max_layoffs,
            'avg_salary': float(avg_salary),
            'bonus_reduction_possible': float(bonus_reduction),
            'min_bonus_level': float(min_bonus_level * 100),
            'reduction_percent': reduction_percent,
        }

        return result

    def predict_cash_flow(self, months_ahead=6):
        predictions = []

        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)

        historical_data = []
        for i in range(6):
            month_date = start_date + timedelta(days=30 * i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0)

            if i < 5:
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            else:
                month_end = end_date

            income = Transaction.objects.filter(
                date__range=[month_start, month_end],
                type__in=['salary', 'bonus', 'advance']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            expenses = Transaction.objects.filter(
                date__range=[month_start, month_end],
                type__in=['tax', 'deduction']
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            balance = BankAccount.objects.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')

            historical_data.append({
                'month': month_start.strftime('%Y-%m'),
                'income': float(income),
                'expenses': float(expenses),
                'balance': float(balance),
            })

        if historical_data:
            avg_income = sum(d['income'] for d in historical_data) / len(historical_data)
            avg_expenses = sum(d['expenses'] for d in historical_data) / len(historical_data)
        else:
            avg_income = 500000
            avg_expenses = 400000

        current_balance = historical_data[-1]['balance'] if historical_data else 1000000

        for i in range(1, months_ahead + 1):
            seasonal_factor = 1.0
            if i in [3, 6]:
                seasonal_factor = 1.2
            elif i in [1, 2]:
                seasonal_factor = 0.95

            projected_income = avg_income * seasonal_factor
            projected_expenses = avg_expenses
            net_flow = projected_income - projected_expenses
            current_balance += net_flow

            predictions.append({
                'month': (datetime.now() + timedelta(days=30 * i)).strftime('%Y-%m'),
                'projected_income': round(projected_income, 2),
                'projected_expenses': round(projected_expenses, 2),
                'projected_balance': round(current_balance, 2),
                'confidence': 0.8 - (i * 0.05),  # Снижение уверенности с каждым месяцем
            })

        result = {
            'balances': predictions,
            'historical_data': historical_data,
            'avg_monthly_income': round(avg_income, 2),
            'avg_monthly_expenses': round(avg_expenses, 2),
            'current_total_balance': round(historical_data[-1]['balance'], 2) if historical_data else 0,
        }

        return result

    def simulate_budget_reduction(self, target_reduction_percent):
        crisis_plan = self.simulate_crisis(target_reduction_percent)

        strategies = {
            'reduce_bonuses': {
                'feasible': crisis_plan['bonus_reduction_possible'] >= crisis_plan['reduction_target'],
                'amount': crisis_plan['bonus_reduction_possible'],
            },
            'layoffs': {
                'feasible': crisis_plan['required_layoffs'] <= crisis_plan['max_possible_layoffs'],
                'layoffs_needed': crisis_plan['required_layoffs'],
            },
            'salary_freeze': {
                'feasible': True,
                'savings_per_month': crisis_plan['avg_salary'] * 0.05,  # 5% экономии при заморозке
            },
        }

        recommended = 'reduce_bonuses'
        if not strategies['reduce_bonuses']['feasible']:
            recommended = 'layoffs'

        result = {
            'target_reduction_percent': target_reduction_percent,
            'total_reduction_needed': crisis_plan['reduction_target'],
            'strategies': strategies,
            'recommended_strategy': recommended,
            'estimated_savings': strategies[recommended].get('amount',
                                                             strategies[recommended].get('savings_per_month', 0)),
        }

        return result

    def analyze_department_efficiency_with_forecast(self, department_id):
        department = Department.objects.get(pk=department_id)

        employments = Employment.objects.filter(department=department, job_type='main')

        stats = employments.aggregate(
            employees_count=Count('id'),
            total_salary=Sum('employee__position__base_salary'),
        )

        total_salary = stats['total_salary'] or Decimal('0.00')
        employees_count = stats['employees_count'] or 0
        avg_salary = total_salary / Decimal(str(employees_count)) if employees_count > 0 else Decimal('0.00')

        efficiency_score = 0.0
        if employees_count > 0:
            efficiency_score = min(100, float(avg_salary) / 1000)

        historical_salaries = []
        for employment in employments[:10]:
            historical_salaries.append({
                'employee_name': employment.employee.name,
                'salary': float(employment.calculate_salary()),
                'position': employment.employee.position.title,
            })

        forecast_3_months = float(avg_salary) * 1.0125

        result = {
            'department_id': department_id,
            'department_name': department.name,
            'enterprise': department.enterprise.name,
            'current_metrics': {
                'employees_count': employees_count,
                'total_monthly_salary': float(total_salary),
                'average_salary': float(avg_salary),
                'efficiency_score': round(efficiency_score, 2),
            },
            'forecast': {
                '3_months_avg_salary': round(forecast_3_months, 2),
                'expected_growth_percent': 5.0,
            },
            'employees': historical_salaries,
        }

        return result