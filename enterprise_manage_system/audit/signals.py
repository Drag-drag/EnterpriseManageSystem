from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog
from decimal import Decimal


def model_to_dict(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name)

        if isinstance(value, Decimal):
            data[field.name] = float(value)
        elif hasattr(value, 'pk') and not isinstance(value, (str, int, float, bool, type(None))):
            data[field.name] = value.pk
        else:
            data[field.name] = value

    return data


def log_change(sender, instance, created, **kwargs):
    from audit.middleware import get_current_user

    if created:
        action_type = 'create'
        old_value = None
        new_value = model_to_dict(instance)
    else:
        action_type = 'update'
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            old_value = model_to_dict(old_instance)
            new_value = model_to_dict(instance)

            if old_value == new_value:
                return
        except sender.DoesNotExist:
            return

    user = get_current_user()

    AuditLog.objects.create(
        user=user,
        action_type=action_type,
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.pk,
        old_value=old_value,
        new_value=new_value,
        description=f"{action_type} {sender.__name__} #{instance.pk}"
    )


def log_delete(sender, instance, **kwargs):
    from audit.middleware import get_current_user

    user = get_current_user()

    AuditLog.objects.create(
        user=user,
        action_type='delete',
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.pk,
        old_value=model_to_dict(instance),
        new_value=None,
        description=f"delete {sender.__name__} #{instance.pk}"
    )


from hr.models import Enterprise, Position, Department, Employee, Employment, Child

models_to_audit = [Enterprise, Position, Department, Employee, Employment, Child]

for model in models_to_audit:
    post_save.connect(log_change, sender=model)
    post_delete.connect(log_delete, sender=model)