# srddl/fields/factories.py - Field factories that use pre-init hook to replace
#                            themselves.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import abc

import srddl.core.fields as scf
import srddl.core.helpers as sch
import srddl.exceptions as se


class FieldFactory(scf.AbstractField):
    @abc.abstractmethod
    def pre_initialize(self, instance):
        pass

    def decode(self, instance, offset):
        raise

    def encode(self, instance, offset, value):
        raise


class SwitchField(FieldFactory):
    DEFAULT = None

    def __init__(self, val, mapping):
        self.val, self.mapping = val, mapping

    def pre_initialize(self, instance):
        val = sch.reference_value(instance, self.val)
        if val in self.mapping:
            return self.mapping[val]
        elif SwitchField.DEFAULT in self.mapping:
            return self.mapping[SwitchField.DEFAULT]
        else:
            raise se.SwitchFieldError(self, val)
