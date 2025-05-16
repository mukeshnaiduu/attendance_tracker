# In a file named custom_filters.py inside your Django app

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Custom template filter to retrieve a value from a dictionary using a key.
    
    Parameters:
        - dictionary: The dictionary from which to retrieve the value.
        - key: The key for which to retrieve the value.
    
    Returns:
        The value corresponding to the key in the dictionary, or None if the key is not found.
    """
    return dictionary.get(str(key))

@register.filter
def pop(dictionary, key):
    """Return a new dictionary with the given key removed."""
    result = dictionary.copy()
    result.pop(key, None)
    return result
