# srddl/fields/padding.py - Padding fields used to fill blanks.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import srddl.core.helpers as sch

from srddl.core.fields import AbstractField, BoundValue

class PaddingValue(BoundValue): pass

class PaddingField(AbstractField):
    Mode = sch.enum(TAKE=0, FILL=1)

    def __init__(self, size, **kwargs):
        super().__init__(self)
        self._mode = kwargs.get('mode', PaddingField.Mode.TAKE)
        self._size = size

    def __get__(self, inst, owner=None):
        return PaddingValue(inst, self._ioffset(inst), self._isize(inst))

    def __set__(self, instance, value):
        pass

    def _isize(self, instance):
        if self._mode == PaddingField.Mode.TAKE:
            return self._size
        elif self._mode == PaddingField.Mode.FILL:
            res = self._size - self._ioffset(instance)
            return res if 0 <= res else 0
        return None
