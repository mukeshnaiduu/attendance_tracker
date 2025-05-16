import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class SpecialCharacterValidator:
    def __init__(self, special_chars="@$#"):
        self.special_chars = special_chars

    def validate(self, password, user=None):
        if not any(char in self.special_chars for char in password):
            raise ValidationError(
                _("Password must contain at least one special character: @, $, or #"),
                code='password_no_special',
            )

    def get_help_text(self):
        return _("Your password must contain at least one special character: @, $, or #") 