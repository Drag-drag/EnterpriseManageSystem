from django.core.exceptions import ValidationError
from django.db import models

class Enterprise(models.Model):
    name = models.CharField(max_length=255, verbose_name='Наименование')
    inn = models.IntegerField(max_length=12, verbose_name='ИНН')
    ogrn = models.IntegerField(max_length=13, verbose_name='ОГРН')
    address = models.TextField(verbose_name='Юридический адрес')

    def __str__(self):
        return self.name

    def get_employee_count(self):
        return Employee.objects.filter(position__enterprise=self).count()

    def print_employees(self):
        return list(Employee.objects.filter(position__enterprise=self))


class Department(models.Model):
    name = models.CharField(max_length=120, verbose_name='Наименование отдела')
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name='departments', verbose_name='Предприятие')
    base_salary_override = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name='Переопределение базовой ставки'
    )

    def __str__(self):
        return f'{self.name} ({self.enterprise.name})'

    def get_effective_salary(self, position_base_salary):
        return self.base_salary_override if self.base_salary_override else position_base_salary


class Position(models.Model):
    title = models.CharField(max_length=120, verbose_name='Наименование должности')
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Базовая ставка')
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, related_name='positions', verbose_name='Предприятие')
    departments = models.ManyToManyField('Department', through='PositionDepartment', related_name='positions', blank=True)

    def __str__(self):
        return f'{self.title} ({self.enterprise.name})'

class PositionDepartment(models.Model):
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    salary_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ['position', 'department']

class EmployeeManager(models.Manager):
    def get_by_position(self, position_title):
        return self.filter(position__title=position_title)

    def sorted_by_name(self):
        return self.order_by('name')

class Employee(models.Model):
    JOB_TYPES = [
        ('main', 'Основное место работы'),
        ('internal', 'Внутреннее совместительство'),
        ('external', 'Внешнее совместительство')
    ]

    name = models.CharField(max_length=120, verbose_name='ФИО')
    age = models.IntegerField(max_length=3, verbose_name='Возраст')
    on_vacation = models.BooleanField(default=False, verbose_name='В отпуске')
    user = models.OneToOneField('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='employee',
                                   verbose_name="Пользователь")
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='employees', verbose_name='Должность')
    _balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name='Баланс')

    objects = EmployeeManager()

    def __str__(self):
        return self.name

    def apply_vacation(self):
        self.on_vacation = True
        self.save()

    @property
    def balance(self):
        return self._balance

    def get_balance(self):
        return self._balance

    def _set_balance(self, value):
        if value < 0:
            raise ValidationError('Баланс не может быть отрицательным.')
        self._balance = value
        self.save()

class Employment(models.Model):
    JOB_TYPE_CHOICES = [
        ('main', 'Основное место работы'),
        ('internal', 'Внутреннее совместительство'),
        ('external', 'Внешнее совместительство')
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='employments', verbose_name='Сотрудник')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, related_name='employments', verbose_name='Отдел')
    external_company = models.CharField(max_length=255, null=True, blank=True, verbose_name='Внешняя компания')
    rate = models.DecimalField(max_digits=3, decimal_places=2, verbose_name='Коэффициент ставки')
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, verbose_name='Тип занятости')
    start_date = models.DateField(auto_now_add=True, verbose_name='Дата начала')
    is_main = models.BooleanField(default=False, verbose_name='Основное место работы')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['employee', 'job_type'], condition=models.Q(job_type='main'),
                                    name='unique_main_job')
        ]

    def clean(self):
        if self.job_type in ['internal', 'external'] and self.rate > 0.5:
            raise ValidationError('Ставка для совместительства не может быть больше 0.5')
        if self.job_type == 'main' and self.rate > 1:
            raise ValidationError('Ставка для основного места не может быть больше 1')
        if self.job_type in ['internal', 'external']:
            if Employment.objects.filter(employee=self.employee, job_type=self.job_type).exists():
                raise ValidationError(f'{self.get_job_type_display()} уже существует для этого сотрудника!')

        if self.job_type == "internal" and not self.department:
            raise ValidationError("Для внутреннего совместительства необходимо указать отдел.")

        if self.job_type == "external" and not self.external_company:
            raise ValidationError("Для внешнего совместительства необходимо указать компанию.")

    def save(self, *args,**kwargs):
        self.clean()

        if self.job_type == 'main':
            Employment.objects.filter(employee=self.employee, job_type='main').update(is_main=False)
            self.is_main = True

        super().save(*args,**kwargs)

    def calculate_salary(self):
        from decimal import Decimal

        if self.job_type == 'main':
            base = self.employee.position.base_salary
        elif self.job_type == 'internal':
            base = self.department.get_effective_salary(self.employee.position.base_salary)
        else:  # external
            base = self.employee.position.base_salary

        base = Decimal(str(base))
        rate = Decimal(str(self.rate))

        return Decimal(base * rate)

    def __str__(self):
        if self.job_type == 'main':
            return f"{self.employee.name} - Основное место ({self.employee.position.title})"
        elif self.job_type == 'internal':
            return f"{self.employee.name} - Внутреннее совместительство ({self.department.name})"
        else:
            return f"{self.employee.name} - Внешнее совместительство ({self.external_company})"


class EmployeeManager(models.Manager):
    def get_by_position(self, position_title):
        return self.filter(position__title=position_title)

    def sorted_by_name(self):
        return self.order_by('name')


class Child(models.Model):
    name = models.CharField(max_length=120, verbose_name='Имя ребенка')
    age = models.IntegerField(max_length=3, verbose_name='Возраст')
    school_number = models.IntegerField(max_length=12, verbose_name='Номер школы')
    parent = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='children', verbose_name='Родитель')

    def __str__(self):
        return self.name

    @property
    def parent_info(self):
        return f"Родитель: {self.parent.name}"

    @property
    def school_info(self):
        return f"Школа №{self.school_number}"

