# test_stage5_with_document.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_project.settings')
django.setup()

from django.contrib.auth.models import User, Group
from hr.models import Enterprise, Department, Position, Employee, Employment
from security.permissions import setup_groups, ROLE_EMPLOYEE
from documents.generator import DocumentGenerator
from ifns.client import send_report

print("=== ЭТАП 5: Генерация документов ===\n")

# Создание групп (обязательно!)
setup_groups()
print(f"✓ Группы созданы")

# Создание структуры
ent = Enterprise.objects.create(name="ООО «Старт»", inn='7701234567', ogrn='1234567890123', address='Москва, ул. Ленина, 1')
print(f"✓ Предприятие: {ent.name}")

dept = Department.objects.create(name="Разработка", enterprise=ent)
print(f"✓ Отдел: {dept.name}")

pos = Position.objects.create(title='Инженер', base_salary=80000, enterprise=ent)
print(f"✓ Должность: {pos.title}")

# Создание пользователя и сотрудника
employee_user = User.objects.create_user('employee', 'emp@test.com', 'emp123')
emp_group = Group.objects.get(name=ROLE_EMPLOYEE)
employee_user.groups.add(emp_group)

emp = Employee.objects.create(name='Иванов Иван', age=28, position=pos, user=employee_user)
print(f"✓ Сотрудник: {emp.name}")

Employment.objects.create(employee=emp, department=dept, rate=1.0, job_type="main")
print(f"✓ Трудоустройство создано")

# Генерация документов
print("\n--- Генерация трудового договора ---")
doc_gen = DocumentGenerator()

contract = doc_gen.generate_contract(employee_id=emp.id)
if contract['success']:
    with open('contract.html', 'w', encoding='utf-8') as f:
        f.write(contract['document'])
    print(f"✓ Трудовой договор сгенерирован и сохранён в contract.html")
    print(f"  Договор №: {contract['context']['contract_number']}")
    print(f"  Сотрудник: {contract['context']['employee_name']}")
    print(f"  Должность: {contract['context']['position']}")
    print(f"  Оклад: {contract['context']['base_salary']} ₽")
else:
    print(f"✗ Ошибка: {contract['error']}")

# Генерация справки 2-НДФЛ
print("\n--- Генерация справки 2-НДФЛ ---")
ndfl = doc_gen.generate_tax_form_2ndfl(employee_id=emp.id, year=2026)
if ndfl['success']:
    with open('2ndfl.html', 'w', encoding='utf-8') as f:
        f.write(ndfl['document'])
    print(f"✓ Справка 2-НДФЛ сгенерирована и сохранена в 2ndfl.html")
    print(f"  Год: {ndfl['year']}")
    print(f"  Общий доход: {ndfl['data']['total_income']} ₽")
    print(f"  Налог: {ndfl['data']['tax_amount']} ₽")
else:
    print(f"✗ Ошибка: {ndfl['error']}")

# Отправка в налоговую
print("\n--- Отправка в ИФНС ---")
status = send_report(ndfl)
print(f"Результат отправки: {status['result']}")
if status['success']:
    print(f"  Квитанция №: {status['receipt_number']}")

print("\n=== Документы сохранены в файлы: contract.html и 2ndfl.html ===")