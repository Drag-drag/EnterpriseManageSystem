from decimal import Decimal
from .models import Employee, Employment


class IncomeCalculator:

    def get_total_income(self, employee: Employee) -> Decimal:
        total = Decimal("0.00")
        employments = employee.employments.all()

        for employment in employments:
            salary = employment.calculate_salary()
            salary = Decimal(str(salary))
            total = total + salary

        return Decimal(total)

    def validate_employment_limits(self, employee: Employee, new_rate: Decimal, job_type: str) -> bool:
        total_rate = Decimal('0.00')

        for employment in employee.employments.all():
            if employment.job_type == job_type:
                return False
            total_rate += Decimal(str(employment.rate))

        total_rate += Decimal(str(new_rate))

        if job_type in ['internal', 'external'] and total_rate > Decimal('1.5'):
            return False

        return True