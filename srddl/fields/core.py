# srddl/fields/core.py - Core fields used everywhere.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import struct

from srddl.core.fields import AbstractField, BoundValue

import srddl.exceptions as se
import srddl.core.helpers as sch

Field_Sizes = sch.enum(BYTE=1, INT16=2, INT32=4, INT64=8)
Field_Endianess = sch.enum(LITTLE='<', BIG='>', NETWORK='!')

class IntValue(BoundValue):
    def __index__(self):
        return self.value

class IntField(AbstractField):
    def __init__(self, *args, **kwargs):
        self._desc = args[0] if len(args) >= 1 else None
        self._size = kwargs.get('size', 1)
        if self._size not in Field_Sizes.values():
            raise ValueError("'size' is not valid.")
        self._signed = kwargs.get('signed', False)
        self._endianess = kwargs.get('endianess', Field_Endianess.LITTLE)
        self._values = dict()
        for it in kwargs.get('values', []):
            self._values[it.value] = it

    def __get__(self, instance, owner=None):
        sig, offset = self._signature(instance), self._ioffset(instance)
        res = IntValue(self, offset, self._isize(instance))
        v = struct.unpack_from(sig, instance.buf, offset)[0]
        res.initialize(self._values.get(v, v))
        return res

    def __set__(self, instance, value):
        sig = self._signature(instance)
        val = ((1 << (self.size(instance) * 8)) - 1) & value
        return struct.pack_into(sig, instance.buf, self._ioffset(instance), val)

    def _isize(self, instance):
        return self._size

    def _signature(self, instance):
        log2 = {1: 0, 2: 1, 4: 2, 8: 3}
        sig = self._endianess + 'bhiq'[log2[self._isize(instance)]]
        return (sig if self._signed else sig.upper())


class ByteArrayValue(BoundValue):
    pass

class ByteArrayField(AbstractField):
    def __init__(self, *args, **kwargs):
        self._desc = args[0] if len(args) >= 1 else None
        self._size = kwargs.get('size', 1)

    def __get__(self, instance, owner=None):
        sig = self._signature(instance)
        res = ByteArrayValue(instance, self._ioffset(instance), self._isize(instance))
        v = struct.unpack_from(sig, instance.buf, self._ioffset(instance))[0]
        res.initialize(v)
        return res

    def __set__(self, instance, value):
        sig, size = self._signature(instance), self._isize(instance)
        val = value.ljust(size, '\x00')
        if len(val) != size:
            raise TypeError()
        struct.pack_into(sig, instance.bug, self._ioffset(instance), val)

    def _isize(self, instance):
        return self._size

    def _signature(self, instance):
        return '{}s'.format(self._isize(instance))
