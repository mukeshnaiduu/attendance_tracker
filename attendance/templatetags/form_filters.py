from django import template
from django.forms import BoundField
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    if not isinstance(field, BoundField):
        return field
    
    return field.as_widget(attrs={
        "class": f"{field.css_classes()} {css_class}".strip()
    })

@register.filter(name='add_placeholder')
def add_placeholder(field, placeholder_text):
    if not isinstance(field, BoundField):
        return field
    
    return field.as_widget(attrs={
        "placeholder": placeholder_text,
        **field.field.widget.attrs
    })

@register.filter(name='add_bootstrap_class')
def add_bootstrap_class(field):
    if not isinstance(field, BoundField):
        return field
    
    css_class = "form-control"
    if field.field.widget.__class__.__name__ in ['CheckboxInput', 'RadioSelect']:
        css_class = "form-check-input"
    
    return field.as_widget(attrs={
        "class": f"{field.css_classes()} {css_class}".strip()
    })

@register.filter(name='field_type')
def field_type(field):
    if not isinstance(field, BoundField):
        return ''
    return field.field.widget.__class__.__name__

@register.filter(name='add_error_class')
def add_error_class(field):
    if not isinstance(field, BoundField):
        return field
    
    if field.errors:
        return field.as_widget(attrs={
            "class": f"{field.css_classes()} is-invalid".strip()
        })
    return field 