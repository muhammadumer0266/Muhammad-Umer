from django import forms
from django.core.validators import MaxLengthValidator, MinLengthValidator

from .guardrails import get_policy
from .services import MAX_QUESTION_LENGTH


class AskForm(forms.Form):
    question = forms.CharField(
        max_length=MAX_QUESTION_LENGTH,
        widget=forms.TextInput(attrs={"aria-describedby": "question-help question-error"}),
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Length limits come from the admin-editable guardrail policy.
        policy = get_policy()
        field = self.fields["question"]
        field.max_length = policy.max_question_length
        field.min_length = policy.min_question_length
        field.validators = [
            MinLengthValidator(policy.min_question_length),
            MaxLengthValidator(policy.max_question_length),
        ]
        field.widget.attrs["maxlength"] = str(policy.max_question_length)
        field.widget.attrs["minlength"] = str(policy.min_question_length)
