from django.contrib import admin
from .models import BankAccount, Transaction, TaxAuthority


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'employee', 'balance', 'currency', 'is_active', 'created_at')
    list_filter = ('currency', 'is_active', 'created_at')
    search_fields = ('account_number', 'employee__name')
    readonly_fields = ('balance', 'created_at')
    raw_id_fields = ('employee',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'type', 'amount', 'currency', 'date', 'description')
    list_filter = ('type', 'currency', 'date')
    search_fields = ('account__employee__name', 'account__account_number', 'description')
    readonly_fields = ('date',)
    raw_id_fields = ('account',)


@admin.register(TaxAuthority)
class TaxAuthorityAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_total_funds')
    filter_horizontal = ('accounts',)

    def get_total_funds(self, obj):
        return obj.get_total_client_funds()

    get_total_funds.short_description = "Общая сумма средств"