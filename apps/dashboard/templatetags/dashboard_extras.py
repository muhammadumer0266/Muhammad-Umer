from django import forms, template

register = template.Library()


@register.filter
def is_checkbox(bound_field) -> bool:
    return isinstance(bound_field.field.widget, forms.CheckboxInput)


@register.filter
def is_wide(bound_field) -> bool:
    """Textareas and multi-checkbox lists span the full form width."""
    return isinstance(bound_field.field.widget, forms.Textarea | forms.CheckboxSelectMultiple)
