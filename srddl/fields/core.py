# srddl/fields/core.py - Core fields used everywhere.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import struct

from srddl.core.abstract import AbstractField

import srddl.exceptions as se
import srddl.core.helpers as sch

Field_Sizes = sch.enum(BYTE=1, INT16=2, INT32=4, INT64=8)
Field_Endianess = sch.enum(LITTLE='<', BIG='>', NETWORK='!')

class Field(AbstractField):
    def __init__(self, *args, **kwargs):
        self._size = kwargs.get('size', 1)
        if self._size not in Field_Sizes.values():
            raise ValueError("'size' is not valid.")
        self._signed = kwargs.get('signed', False)
        self._endianess = kwargs.get('endianess', Field_Endianess.LITTLE)

    def __get__(self, instance, owner=None):
        sig = self._signature()
        return struct.unpack_from(sig, instance.buf, self.offset(instance))[0]

    def __set__(self, instance, value):
        sig, val = self._signature(), ((1 << (self._size * 8)) - 1) & value
        return struct.pack_into(sig, instance.buf, self.offset(instance), val)

    def size(self, instance):
        return self._size

    def _signature(self):
        log2 = {1: 0, 2: 1, 4: 2, 8: 3}
        sig = self._endianess + 'bhiq'[log2[self._size]]
        return (sig if self._signed else sig.upper())
