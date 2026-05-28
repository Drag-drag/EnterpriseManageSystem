from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError
from hr.models import Employee

from decimal import Decimal

class BankAccount(models.Model):
    CURRENCY_CHOICES = [
        ('RUB', 'Российский рубль'),
        ('USD', 'Доллар США'),
        ('EUR', 'Евро')
    ]
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='bank_account', verbose_name='Сотрудник')
    account_number = models.CharField(max_length=20, unique=True, verbose_name='Номер счёта')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='RUB', verbose_name='Валюта')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='Баланс')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_active = models.BooleanField(default=True, verbose_name='Счёт активен')

    def update_balance(self, amount):
        self.balance += float(amount)
        return self.save()

    def __str__(self):
        return f'Счёт {self.account_number}  - {self.employee.name}'


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('salary', 'Начисление зарплаты'),
        ('advance', 'Аванс'),
        ('bonus', 'Премия'),
        ('tax', 'Налоговый вычет'),
        ('compensation', 'Компенсация'),
    ]
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions', verbose_name='Счёт')
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name='Тип операции')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Сумма')
    description = models.TextField(verbose_name="Описание")
    date = models.DateTimeField(auto_now_add=True, verbose_name='Дата операции')
    currency = models.CharField(max_length=3, default='RUB', verbose_name='Валюта')

    class Meta:
        ordering = ['-date']

    def clean(self):
        if self.amount <= 0:
            raise ValidationError('Сумма транзакции должна быть положительной')
        if self.type == 'tax' and self.amount > self.account.balance:
            raise ValidationError('Недостаточно средств на счете')

    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} {self.currency} - {self.date}"


class TaxAuthorityManager(models.Manager):
    def with_employee_data(self):
        return self.select_related('employee').prefetch_related('employee__employments')

    def get_active_accounts(self):
        self.filter(is_active=True).select_related('employee')

class TaxAuthority(models.Model):
    name = models.CharField(max_length=255, default='Федеральная налоговая служба', verbose_name='Наименование')
    accounts = models.ManyToManyField(BankAccount, related_name='tax_authorities', verbose_name='Счета')

    objects = TaxAuthorityManager()

    def get_total_client_funds(self):
        total = self.accounts.aggregate(total=Sum('balance'))['total']
        return total or 0


    def get_all_accounts(self):
        return TaxAuthority.objects.get_active_accounts()


