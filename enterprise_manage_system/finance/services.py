from decimal import Decimal
from importlib.metadata import distribution

from django.db import transaction as db_transaction
from django.db.models import Sum
from hr.models import Employee, Employment
from hr.services import IncomeCalculator
from .models import BankAccount, Transaction, TaxAuthority


class PaymentService:
    def __init__(self):
        self.income_calculator = IncomeCalculator()

    def calculate_total_income(self, employee: Employee) -> Decimal:
        return self.income_calculator.get_total_income(employee)

    def distributive_payment(self, employee: Employee, total_amount: Decimal) -> dict:
        employments = employee.employments.all()
        total_rate = sum(emp.rate for emp in employments)

        distribution = {}
        for employment in employments:
            if total_rate > 0:
                proportion = employment.rate / total_rate
                amount = total_amount * proportion
                distribution[employment] = {
                    'amount': amount,
                    'rate': employment.rate,
                    'department': employment.department.name if employment.department else None,
                    'external company': employment.external_company
                }

        return distribution


    @db_transaction.atomic
    def process_payroll(self, employee: Employee, transaction_type: str, description: str) -> dict:
        try:
            total_income = self.calculate_total_income(employee)
            total_income = Decimal(str(total_income))

            if total_income <= 0:
                return {'success': False, 'error': 'Сумма выплаты должна быть положительной'}

            bank_account = employee.bank_account
            distribution = self.distributive_payment(employee, total_income)

            transactions = []
            for job_type, data in distribution.items():
                transaction = Transaction.objects.create(
                    account=bank_account,
                    type=transaction_type,
                    amount=data['amount'],
                    description=f'{description} - {job_type}'
                )
                transactions.append(transaction)

            bank_account.update_balance(Decimal(total_income))

            return {
                'success': True,
                'total_amount': total_income,
                'transactions': transactions,
                'new_balance': bank_account.balance
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @db_transaction.atomic
    def process_bonus(self, employee: Employee, bonus_amount: Decimal, description: str) -> dict:
        try:
            if bonus_amount <= 0:
                return {'success': False, 'error': 'Сумма премии должна быть положительной'}

            bank_account = employee.bank_account
            transaction = Transaction.objects.create(
                account=bank_account,
                type='bonus',
                amount=bonus_amount,
                description=description,
            )
            bank_account.update_balance(bonus_amount)

            return {
                'success': True,
                'amount': bonus_amount,
                'transaction': transaction,
                'new_balance': bank_account.balance
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}


class TaxService:
    def __init__(self):
        self.tax_authority, _ = TaxAuthority.objects.get_or_create(name='Федеральная налоговая служба')

    def register_account(self, bank_account: BankAccount):
        self.tax_authority.accounts.add(bank_account)

    def get_total_taxable_funds(self) -> Decimal:
        return self.tax_authority.get_total_client_funds()

    def get_accounts_summary(self) -> dict:
        accounts = self.tax_authority.accounts.select_related('employee').all()

        summary = {
            'total_accounts': accounts.count(),
            'total_balance': Decimal('0.00'),
            'accounts': []
        }

        for account in accounts:
            summary['total_balance'] += account.balance
            summary['accounts'].append({
                'account_number': account.account_number,
                'employee_name': account.employee.name,
                'balance': account.balance,
                'currency': account.currency
            })

        return summary
