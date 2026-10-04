from django.contrib import admin

from .models import AskLog, DailyBudget, RagChunk, RagDocument


class RagChunkInline(admin.TabularInline):
    model = RagChunk
    extra = 0
    readonly_fields = ["text", "token_count"]
    fields = ["text", "token_count"]
    can_delete = False

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(RagDocument)
class RagDocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "source_type", "source_id", "updated_at"]
    list_filter = ["source_type"]
    search_fields = ["title", "source_id"]
    readonly_fields = ["content_hash", "created_at", "updated_at"]
    inlines = [RagChunkInline]

    def has_add_permission(self, request) -> bool:
        return False


@admin.register(AskLog)
class AskLogAdmin(admin.ModelAdmin):
    list_display = ["question", "refused", "latency_ms", "created_at"]
    list_filter = ["refused", "created_at"]
    search_fields = ["question"]
    readonly_fields = [f.name for f in AskLog._meta.fields]

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False


@admin.register(DailyBudget)
class DailyBudgetAdmin(admin.ModelAdmin):
    list_display = ["date", "spent_usd"]
    readonly_fields = ["date"]

    def has_add_permission(self, request) -> bool:
        return False
