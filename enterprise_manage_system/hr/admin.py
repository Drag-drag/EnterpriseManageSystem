from django.contrib import admin
from .models import Enterprise, Position, Department, Employee, Employment, Child

@admin.register(Enterprise)
class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ('name', 'inn', 'ogrn', 'address')
    list_filter = ('name', 'inn')

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'base_salary', 'enterprise')
    list_filter = ('enterprise',)
    search_fields = ('title',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'enterprise', 'base_salary_override')
    list_filter = ('enterprise',)
    search_fields = ('name',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'on_vacation', 'position')
    list_filter = ('position', 'on_vacation')
    search_fields = ('name',)
    actions = ['activate_vacation']
    readonly_fields = ('balance',)

    @admin.action(description="Активировать отпуск у выбранных сотрудников")
    def activate_vacation(self, request, queryset):
        queryset.update(on_vacation=True)

@admin.register(Employment)
class EmploymentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'job_type', 'rate', 'department', 'external_company', 'start_date', 'is_main')
    list_filter = ('job_type', 'is_main', 'start_date')
    search_fields = ('employee__name', 'external_company')
    raw_id_fields = ('employee', 'department')

@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'school_number', 'parent')
    list_filter = ('parent',)
    search_fields = ('name', 'school_number')

