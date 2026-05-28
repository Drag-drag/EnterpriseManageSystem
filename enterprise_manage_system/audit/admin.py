from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action_type', 'content_type', 'object_id', 'description')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('user__username', 'description')
    readonly_fields = ('timestamp', 'user', 'action_type', 'content_type', 'object_id', 'old_value', 'new_value',
                       'description')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

