from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.serializers.json import DjangoJSONEncoder


class AuditLog(models.Model):
    ACTION_TYPES = [
        ('create', 'Создание'),
        ('update', 'Обновление'),
        ('delete', 'Удаление'),
        ('view', 'Просмотр'),
        ('login', 'Вход'),
        ('logout', 'Выход'),
        ('access_denied', 'Отказ в доступе'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время события")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пользователь")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP-адрес")
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name="Тип операции")

    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name="Тип объекта")
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID объекта")
    content_object = GenericForeignKey('content_type', 'object_id')

    old_value = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True, verbose_name="Значение до изменения")
    new_value = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True,
                                 verbose_name="Значение после изменения")

    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Журнал аудита"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'action_type']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.timestamp} - {self.get_action_type_display()} - {self.user}"

    @classmethod
    def get_history(cls, **filters):
        return cls.objects.filter(**filters)


class AuditLogManager(models.Manager):
    def get_for_object(self, obj):
        content_type = ContentType.objects.get_for_model(obj)
        return self.filter(content_type=content_type, object_id=obj.pk)

    def get_by_user(self, user):
        return self.filter(user=user)

    def get_recent(self, days=7):
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(timestamp__gte=cutoff)