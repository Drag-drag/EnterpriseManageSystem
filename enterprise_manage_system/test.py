import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_project.settings')
django.setup()

from decimal import Decimal
from simulation.engine import BusinessSimulator
from hr.models import Enterprise, Department, Position, Employee, Employment
from finance.models import BankAccount, Transaction

print("=== ЭТАП 6: Прогностический модуль и стресс-тестирование ===\n")

# 1. Создание тестовых данных
print("--- Подготовка тестовых данных ---")

ent = Enterprise.objects.create(
    name="ООО «Прогноз»",
    inn="7701999888",
    ogrn="1234567890777",
    address="Москва, ул. Будущего, 1"
)
print(f"✓ Создано предприятие: {ent.name}")

dept1 = Department.objects.create(name="Аналитика", enterprise=ent)
dept2 = Department.objects.create(name="Разработка", enterprise=ent)

pos1 = Position.objects.create(title="Аналитик", base_salary=90000, enterprise=ent)
pos2 = Position.objects.create(title="Разработчик", base_salary=120000, enterprise=ent)

# Создание сотрудников
employees_data = [
    ("Иванов Иван", 30, pos1, dept1),
    ("Петров Петр", 28, pos1, dept1),
    ("Сидорова Анна", 32, pos2, dept2),
    ("Козлов Дмитрий", 35, pos2, dept2),
    ("Смирнова Елена", 29, pos1, dept1),
]

for name, age, pos, dept in employees_data:
    emp = Employee.objects.create(name=name, age=age, position=pos)
    Employment.objects.create(employee=emp, department=dept, rate=1.0, job_type="main")
    # Создание банковского счета
    BankAccount.objects.get_or_create(employee=emp, defaults={
        'account_number': f"40817{hash(name) % 10000000000:010d}",
        'balance': 100000
    })

print(f"✓ Создано {len(employees_data)} сотрудников")

# 2. Создание тестовых транзакций для прогноза
print("\n--- Создание исторических транзакций ---")

from datetime import datetime, timedelta
from decimal import Decimal
# В test_stage6.py при создании транзакций используйте timezone.now()
from django.utils import timezone

employees = Employee.objects.all()
for i in range(6):  # 6 месяцев истории
    month_date = timezone.now() - timedelta(days=30 * (6 - i))
    for emp in employees:
        employment = emp.employments.filter(job_type='main').first()
        if employment:
            salary = employment.calculate_salary()
            account = BankAccount.objects.get(employee=emp)

            Transaction.objects.create(
                account=account,
                type='salary',
                amount=salary,
                description=f"Зарплата за {month_date.strftime('%B')}",
                date=month_date
            )
print("✓ Созданы исторические транзакции")

# 3. Сценарий массового найма
print("\n--- Сценарий массового найма ---")
sim = BusinessSimulator()

hiring_impact = sim.simulate_mass_hiring(count=10, department_id=dept1.id)
print(f"Изменение фонда оплаты труда: {hiring_impact['payroll_delta']} ₽")
print(f"Изменение налоговой нагрузки: {hiring_impact['tax_delta']} ₽")
print(f"Новых сотрудников: {hiring_impact['new_employees_count']}")
print(f"Ежемесячное увеличение ФОТ: {hiring_impact['monthly_payroll_increase']} ₽")

# 4. Сценарий сокращения бюджета
print("\n--- Сценарий сокращения бюджета (кризис) ---")
crisis_plan = sim.simulate_crisis(reduction_percent=20)
print(f"Текущий ФОТ: {crisis_plan['current_payroll']} ₽")
print(f"Цель сокращения: {crisis_plan['reduction_target']} ₽")
print(f"Необходимые сокращения: {crisis_plan['required_layoffs']} чел.")
print(f"Максимально возможных сокращений: {crisis_plan['max_possible_layoffs']} чел.")
print(f"Средняя зарплата: {crisis_plan['avg_salary']} ₽")

# 5. Прогноз денежных потоков
print("\n--- Прогноз денежных потоков ---")
forecast = sim.predict_cash_flow(months_ahead=6)
print(f"Среднемесячный доход: {forecast['avg_monthly_income']} ₽")
print(f"Среднемесячные расходы: {forecast['avg_monthly_expenses']} ₽")
print("Прогноз по месяцам:")
for month in forecast['balances']:
    print(
        f"  {month['month']}: баланс = {month['projected_balance']} ₽ (уверенность: {month['confidence'] * 100:.0f}%)")

# 6. Анализ стратегий сокращения бюджета
print("\n--- Анализ стратегий сокращения бюджета ---")
budget_analysis = sim.simulate_budget_reduction(target_reduction_percent=20)
print(f"Цель: сократить бюджет на {budget_analysis['target_reduction_percent']}%")
print(f"Необходимо сократить: {budget_analysis['total_reduction_needed']} ₽")
print("Доступные стратегии:")
for strategy, data in budget_analysis['strategies'].items():
    print(f"  - {strategy}: выполнимо = {data['feasible']}")
print(f"Рекомендуемая стратегия: {budget_analysis['recommended_strategy']}")

# 7. Анализ эффективности подразделений с прогнозом
print("\n--- Анализ эффективности подразделений ---")
dept_analysis = sim.analyze_department_efficiency_with_forecast(department_id=dept1.id)
print(f"Отдел: {dept_analysis['department_name']}")
print(f"  Сотрудников: {dept_analysis['current_metrics']['employees_count']}")
print(f"  ФОТ: {dept_analysis['current_metrics']['total_monthly_salary']} ₽")
print(f"  Средняя зарплата: {dept_analysis['current_metrics']['average_salary']} ₽")
print(f"  Эффективность: {dept_analysis['current_metrics']['efficiency_score']} / 100")
print(f"  Прогноз средней зарплаты (3 мес): {dept_analysis['forecast']['3_months_avg_salary']} ₽")

# 8. Проверка массового найма с другой должностью
print("\n--- Массовый найм на конкретную должность ---")
hiring_impact_pos = sim.simulate_mass_hiring(count=5, position_id=pos1.id)
print(f"Найм 5 {pos1.title}: +{hiring_impact_pos['payroll_delta']} ₽ к ФОТ")

# 9. Проверка кэширования
print("\n--- Проверка кэширования Redis ---")
# Первый вызов (кэширует)
import time

start = time.time()
hiring_impact_cached = sim.simulate_mass_hiring(count=10, department_id=dept1.id)
first_call = time.time() - start

# Второй вызов (из кэша)
start = time.time()
hiring_impact_cached2 = sim.simulate_mass_hiring(count=10, department_id=dept1.id)
second_call = time.time() - start

print(f"Первый вызов: {first_call:.4f} сек")
print(f"Второй вызов (из кэша): {second_call:.4f} сек")
if second_call < first_call:
    print("✓ Кэширование работает")

print("\n=== ВСЕ ПРОВЕРКИ ЭТАПА 6 УСПЕШНО ЗАВЕРШЕНЫ ===")