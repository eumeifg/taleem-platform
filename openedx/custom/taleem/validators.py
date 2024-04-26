from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _


class ConsecutiveRepeatingCharacterValidator:
    def __init__(self, min_length=3):
        self.length = min_length

    def validate(self, password, user=None):
        unique_characters = password.join(set(password))
        for character in unique_characters:
            if password.count(character) >= self.length:
                check_character = "".join(character * self.length)
                if check_character in password:
                    raise ValidationError(
                        _("The password contains characters that are consecutively repeating, e.g 1111 or aaaa")
                    )

    def get_help_text(self):
        return (
            _("Characters in the password cannot consecutively repeat, e.g 1111 or aaaa")
        )


class ConsecutiveIncreasingCharacterValidator:
    def __init__(self, min_length=3):
        self.length = min_length

    def validate(self, password, user=None):
        for character in password:
            if character.isalnum():
                count = 1
                asci_code = ord(character)
                index = password.index(character)

                for i in range(1, self.length):
                    if index < len(password) - i and password[index + i].isalnum():
                        next_asci_code = ord(password[index + i])
                        if next_asci_code == asci_code + 1:
                            count += 1
                            asci_code += 1

                        if count >= self.length:
                            raise ValidationError(
                                _("The password contains consecutively increasing integers, e.g 12345 or abcda")
                            )

    def get_help_text(self):
        return _("Characters in the password cannot contain consecutively increasing integers, e.g 12345 or abcda")


class ConsecutiveDecreasingCharacterValidator:
    def __init__(self, min_length=3):
        self.length = min_length

    def validate(self, password, user=None):
        for character in password:
            if character.isalnum():
                count = 1
                asci_code = ord(character)
                index = password.index(character)

                for i in range(1, self.length):
                    if index < len(password) - i and password[index + i].isalnum():
                        next_asci_code = ord(password[index + i])
                        if next_asci_code == asci_code - 1:
                            count += 1
                            asci_code -= 1

                        if count >= self.length:
                            raise ValidationError(
                                _("The password contains consecutively decreasing integers, e.g 54321 or dcba")
                            )

    def get_help_text(self):
        return _("Characters in the password cannot contain consecutively decreasing integers, e.g 54321 or dcba")


class ContextValidator:

    def validate(self, password, user=None):
        WORDS_NOT_ALLOWED_IN_PASSWORD = settings.WORDS_NOT_ALLOWED_IN_PASSWORD

        for word in WORDS_NOT_ALLOWED_IN_PASSWORD:
            if word in password or word.upper() in password:
                raise ValidationError(_("Password contains not allowed word."))

    def get_help_text(self):
        return _("Password cannot contain not allowed word.")
