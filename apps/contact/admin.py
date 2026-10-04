from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "status", "spam_score", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["name", "email", "message"]
    readonly_fields = ["name", "email", "message", "ip_hash", "user_agent_hash", "created_at"]

    def has_add_permission(self, request) -> bool:
        return False
