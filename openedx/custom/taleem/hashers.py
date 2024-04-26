import hashlib
from collections import OrderedDict

from django.utils.crypto import constant_time_compare
from django.contrib.auth.hashers import mask_hash, BasePasswordHasher
from django.utils.translation import gettext_noop as _

class SimpleSHA1PasswordHasher(BasePasswordHasher):
    """
    Secure password hashing using the SHA1 algorithm
    to support Newton users having SHA1 hash without salt.
    """
    algorithm = "simple_sha1"
    digest = hashlib.sha1

    def encode(self, password, salt=None, iterations=None):
        assert password is not None
        hash = hashlib.sha1(password.encode()).hexdigest()
        return "%s$%s" % (self.algorithm, hash)

    def verify(self, password, encoded):
        algorithm, hash = encoded.split('$', 2)
        assert algorithm == self.algorithm
        encoded_2 = self.encode(password)
        return constant_time_compare(encoded, encoded_2)

    def safe_summary(self, encoded):
        algorithm, hash = encoded.split('$', 2)
        assert algorithm == self.algorithm
        return OrderedDict([
            (_('algorithm'), algorithm),
            (_('hash'), mask_hash(hash)),
        ])

    def harden_runtime(self, password, encoded):
        return

