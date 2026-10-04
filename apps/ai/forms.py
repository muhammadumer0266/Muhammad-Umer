from django import forms

from .services import MAX_QUESTION_LENGTH


class AskForm(forms.Form):
    question = forms.CharField(
        max_length=MAX_QUESTION_LENGTH,
        widget=forms.TextInput(attrs={"aria-describedby": "question-error"}),
    )
