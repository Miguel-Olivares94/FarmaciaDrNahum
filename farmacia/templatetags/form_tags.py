from django import template
from django.forms import CheckboxInput, RadioSelect, FileInput

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Filtro para agregar clases CSS a los campos de formulario de Django.
    Uso: {{ form.campo|add_class:"form-control form-control-lg" }}
    """
    # Si es un campo de checkbox o radio, no agregar form-control
    if isinstance(field.field.widget, (CheckboxInput, RadioSelect)):
        return field.as_widget(attrs={'class': css_class})
    
    # Para campos de archivo, agregar form-control pero sin lg
    if isinstance(field.field.widget, FileInput):
        return field.as_widget(attrs={'class': 'form-control'})
    
    # Para todos los otros campos (text, email, number, select, etc)
    existing_class = field.field.widget.attrs.get('class', '')
    
    if existing_class:
        full_class = f"{existing_class} {css_class}"
    else:
        full_class = css_class
    
    return field.as_widget(attrs={'class': full_class})

@register.filter(name='add_placeholder')
def add_placeholder(field, placeholder_text):
    """
    Filtro para agregar placeholder a los campos de formulario.
    Uso: {{ form.campo|add_placeholder:"Escriba el nombre..." }}
    """
    return field.as_widget(attrs={'placeholder': placeholder_text})

@register.filter(name='add_attrs')
def add_attrs(field, attrs_string):
    """
    Filtro para agregar múltiples atributos a los campos.
    Uso: {{ form.campo|add_attrs:"data-test=true|aria-label=Campo" }}
    """
    attrs = {}
    if attrs_string:
        for attr_pair in attrs_string.split('|'):
            if '=' in attr_pair:
                key, value = attr_pair.split('=', 1)
                attrs[key.strip()] = value.strip()
    
    return field.as_widget(attrs=attrs)
