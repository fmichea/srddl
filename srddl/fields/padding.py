# srddl/fields/padding.py - Padding fields used to fill blanks.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import srddl.core.fields as scf
import srddl.core.helpers as sch

class PaddingBoundValue(scf.BoundValue):
    def _size(self, flags):
        if self._field._mode == PaddingField.Mode.TAKE:
            return self._field._size
        elif self._field._mode == PaddingField.Mode.FILL:
            res = self._field._size - self._offset
            return res if 0 <= res else 0
        return None

class PaddingField(scf.AbstractField):
    Mode = sch.enum(TAKE=0, FILL=1)

    class Meta:
        boundvalue_class = PaddingBoundValue

    def __init__(self, size, **kwargs):
        super().__init__()
        self._mode = kwargs.get('mode', PaddingField.Mode.TAKE)
        self._size = size

    def decode(self, data, offset):
        return None

    def encode(self, data, offset, value):
        pass
