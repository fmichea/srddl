# srddl/fields/padding.py - Padding fields used to fill blanks.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import srddl.core.helpers as sch

from srddl.core.fields import AbstractField, BoundValue

PaddingMode = sch.enum(TAKE=0, FILL=1)

class PaddingValue(BoundValue): pass

class PaddingField(AbstractField):
    def __init__(self, size, **kwargs):
        self._size, self._mode = size, kwargs.get('mode', PaddingMode.TAKE)

    def __get__(self, inst, owner=None):
        return PaddingValue(inst, self._ioffset(inst), self._isize(inst))

    def __set__(self, instance, value):
        pass

    def _isize(self, instance):
        if self._mode == PaddingMode.TAKE:
            return self._size
        elif self._mode == PaddingMode.FILL:
            res = self._size - self._ioffset(instance)
            return res if 0 <= res else 0
        return None
