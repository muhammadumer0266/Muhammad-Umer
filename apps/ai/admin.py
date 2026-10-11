from django.contrib import admin

from .models import AskLog, DailyBudget, GuardrailPolicy, GuardrailRule, RagChunk, RagDocument


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
    list_display = ["question", "refused", "guardrail", "latency_ms", "created_at"]
    list_filter = ["refused", "created_at"]
    search_fields = ["question", "guardrail"]
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


@admin.register(GuardrailPolicy)
class GuardrailPolicyAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "enabled",
        "max_question_length",
        "similarity_threshold",
        "updated_at",
    ]
    fieldsets = [
        ("Availability", {"fields": ["enabled", "disabled_message", "rate_limit_per_hour"]}),
        ("Questions", {"fields": ["min_question_length", "max_question_length"]}),
        ("Retrieval", {"fields": ["similarity_threshold", "top_k"]}),
        (
            "Answers",
            {"fields": ["require_citations", "redact_pii", "max_answer_chars"]},
        ),
        ("Messages", {"fields": ["refusal_message", "no_answer_message"]}),
    ]

    def has_add_permission(self, request) -> bool:
        return not GuardrailPolicy.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(GuardrailRule)
class GuardrailRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "stage", "match_type", "pattern", "action", "is_active", "hit_count"]
    list_editable = ["is_active"]
    list_filter = ["stage", "action", "is_active", "match_type"]
    search_fields = ["name", "pattern"]
    readonly_fields = ["hit_count", "created_at", "updated_at"]
