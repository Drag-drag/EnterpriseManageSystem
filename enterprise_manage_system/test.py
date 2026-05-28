import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_project.settings')
django.setup()

from decimal import Decimal
from django.contrib.auth.models import User
from audit.models import AuditLog
from audit.middleware import _thread_locals
from reports.services import ReportGenerator
from tasks.payroll import run_payday_task, run_tax_transfer_task, run_vacation_check_task
from hr.models import Enterprise, Department, Position, Employee, Employment
from finance.models import BankAccount

print("=== ЭТАП 4: Аналитика, Аудит и Автоматизация ===\n")

# Установка текущего пользователя для аудита
user, created = User.objects.get_or_create(username='admin')
_thread_locals.user = user

# 1. Создание тестовых данных
print("--- Подготовка тестовых данных ---")

ent = Enterprise.objects.create(
    name="ООО «Аналитика»",
    inn="77015551234",
    ogrn="1234567890555",
    address="Москва, ул. Аналитическая, 15"
)
print(f"✓ Создано предприятие: {ent.name}")

dept1 = Department.objects.create(name="Разработка", enterprise=ent)
dept2 = Department.objects.create(name="Тестирование", enterprise=ent)
print(f"✓ Созданы отделы: {dept1.name}, {dept2.name}")

pos = Position.objects.create(title="Разработчик", base_salary=100000, enterprise=ent)
print(f"✓ Создана должность: {pos.title}")

emp1 = Employee.objects.create(name="Иванов Иван", age=30, position=pos)
emp2 = Employee.objects.create(name="Петров Петр", age=25, position=pos)
print(f"✓ Созданы сотрудники: {emp1.name}, {emp2.name}")

Employment.objects.create(employee=emp1, department=dept1, rate=1.0, job_type="main")
Employment.objects.create(employee=emp2, department=dept2, rate=1.0, job_type="main")
print("✓ Созданы трудоустройства")

# 2. Проверка аудита
print("\n--- Проверка журнала аудита ---")

history = AuditLog.objects.filter(content_type__model='employee')
print(f"Записей в журнале по сотрудникам: {history.count()}")

if history.exists():
    latest = history.first()
    print(f"Последнее действие: {latest.get_action_type_display()} - {latest.description}")
    print(f"  Время: {latest.timestamp}")

# 3. Проверка отчета по зарплатам
print("\n--- Отчет по зарплатам ---")
report_gen = ReportGenerator()
payroll_report = report_gen.generate_payroll_report(month="2026-04")
print(f"Фонд оплаты труда: {payroll_report['total_fund']} ₽")
print(f"Количество сотрудников: {payroll_report['employees_count']}")
print("Детализация:")
for detail in payroll_report['details'][:3]:
    print(f"  - {detail['employee_name']}: {detail['salary']} ₽")

# 4. Проверка налогового отчета
print("\n--- Налоговый отчет ---")
tax_report = report_gen.generate_tax_report()
print(f"Общий фонд зарплат: {tax_report['total_salary_fund']} ₽")
print(f"НДФЛ (13%): {tax_report['total_ndfl']} ₽")

# 5. Проверка эффективности отделов
print("\n--- Эффективность подразделений ---")
efficiency = report_gen.generate_department_efficiency_report()
for dept_data in efficiency:
    print(f"  {dept_data['department_name']}: {dept_data['employees_count']} сотр., ФОТ: {dept_data['total_salary_fund']} ₽")

# 6. Проверка финансового отчета
print("\n--- Финансовый отчет ---")
financial_report = report_gen.generate_financial_report()
print(f"Активных счетов: {financial_report['active_accounts']}")
print(f"Общий баланс: {financial_report['total_balance']} ₽")

# 7. Имитация фоновых задач
print("\n--- Фоновые задачи (имитация Celery) ---")
print("Задача выплаты зарплаты:")
payroll_result = run_payday_task()
print(f"  Результат: выполнено {len(payroll_result)} выплат")

print("\nЗадача перевода налогов:")
tax_result = run_tax_transfer_task()

print("\nЗадача проверки отпусков:")
vacation_result = run_vacation_check_task()
print(f"  Могут уйти в отпуск: {vacation_result['can_take_vacation']}")

# 8. Проверка истории аудита по объекту
print("\n--- История аудита для сотрудника ---")
emp_history = AuditLog.get_history(object_id=emp1.id)
print(f"Количество записей для {emp1.name}: {emp_history.count()}")

print("\n=== ВСЕ ПРОВЕРКИ ЭТАПА 4 УСПЕШНО ЗАВЕРШЕНЫ ===")