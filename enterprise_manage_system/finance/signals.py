from django.db.models.signals import post_save
from django.dispatch import receiver
from hr.models import Employee
from .models import BankAccount
import random

@receiver(post_save, sender=Employee)
def create_bank_account(sender, instance, created, **kwargs):
    if created:
        account_number = f"12345{random.randint(1000000000, 9999999999)}"
        BankAccount.objects.create(
            employee=instance,
            account_number=account_number,
            balance=0.00
        )
