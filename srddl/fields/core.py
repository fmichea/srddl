# srddl/fields/core.py - Core fields used everywhere.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import srddl.core.fields as scf
import srddl.core.helpers as sch
import srddl.core.offset as sco
import srddl.exceptions as se


class AbstractField(scf.AbstractField):
    def initialize(self, instance, *args, **kwargs):
        raise se.AbstractStructError(instance)

    def decode(self, instance, offset):
        raise se.AbstractStructError(instance)

    def encode(self, instance, offset, value):
        raise se.AbstractStructError(instance)


class IntFieldBoundValue(scf.BoundValue):
    def __index__(self):
        return self._value


class IntField(scf.AbstractField):
    Size = sch.enum(BYTE=1, INT8=1, INT16=2, INT32=4, INT64=8)
    Endianess = sch.enum(LITTLE='<', BIG='>', NETWORK='!')
    Base = sch.enum(BIN=2, OCT=8, DEC=10, HEX=16)

    class Meta:
        boundvalue_class = IntFieldBoundValue

    def __init__(self, *args, **kwargs):
        if not hasattr(self, '_size'):
            self._size = kwargs.pop('size', IntField.Size.BYTE)
            if self._size not in IntField.Size.values():
                raise ValueError("'size' is not valid.")
        if not hasattr(self, '_base'):
            self._base = kwargs.pop('base', IntField.Base.DEC)
            if self._base not in IntField.Base.values():
                raise ValueError("'base' is not valid.")
        self._signed = kwargs.pop('signed', False)
        self._endianess = kwargs.pop('endianess', IntField.Endianess.LITTLE)
        self._values = dict()
        for it in kwargs.pop('values', []):
            self._values[it['value']] = it
        super().__init__(*args, **kwargs)

    def decode(self, instance, offset):
        size = self.__get__(instance)['size']
        res = instance['data'].unpack_from(self._sig(size), offset.byte)[0]
        return self._values.get(res, res)

    def encode(self, instance, offset, value):
        size = self.__get__(instance)['size']
        instance['data'].pack_into(self._sig(size), offset.byte, value)

    def _sig(self, size):
        log2 = {1: 0, 2: 1, 4: 2, 8: 3}
        sig = self._endianess + 'bhiq'[log2[size.byte]]
        return (sig if self._signed else sig.upper())

    def _display_value(self, value):
        formats = {
            IntField.Base.BIN: '{:#b}', IntField.Base.OCT: '{:#o}',
            IntField.Base.DEC: '{}', IntField.Base.HEX: '{:#x}',
        }
        return formats.get(self._base, '{}').format(value)


class ByteArrayField(scf.AbstractField):
    def __init__(self, size, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._size = size

    def decode(self, instance, offset):
        size = self.__get__(instance)['size']
        return instance['data'].unpack_from(self._sig(size), offset.byte)[0]

    def encode(self, instance, offset, value):
        size = self.__get__(instance)['size']
        value = value.ljust(size.byte, '\x00')[:size.byte]
        instance['data'].pack_into(self._sig(size), offset.byte, value)

    def _sig(self, size):
        return '{}s'.format(size.byte)


class BitFieldBoundValue(IntFieldBoundValue):
    @property
    def _size(self):
        size = sch.reference_value(self._instance, self._field._size)
        if not (0 < size < 8):
            return se.BifFieldSizeError(size)
        return sco.Size(bit=size)


class BitField(scf.AbstractField):
    class Meta:
        aligned = False
        boundvalue_class = BitFieldBoundValue

    def __init__(self, size, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._size = size

    def decode(self, instance, offset):
        size = self.__get__(instance)['size']
        i = instance['data'].unpack_from('>H', offset.byte)[0]
        mask = self._mask(size) << self._mask_offset(offset.bit, size)
        return ((i & mask) >> self._mask_offset(offset.bit, size))

    def encode(self, instance, offset, value):
        size = self.__get__(instance)['size']
        i = instance['data'].unpack_from('>H', offset.byte)[0]
        mask = self._mask(size) << self._mask_offset(offset.bit, size)
        res = (i & ((~mask) & 0xffff))
        res |= (value & self._mask(size)) << self._mask_offset(offset.bit, size)
        instance['data'].pack_into('>H', offset.byte, res)

    def _mask(self, size):
        return ((1 << size.bit) - 1)

    def _mask_offset(self, bit, size):
        return (16 - bit - size.bit)


class BitMaskField(IntField):
    class Meta: pass

    def decode(self, instance, offset):
        nb = super().decode(instance, offset)
        if isinstance(nb, scf.Value):
            return [nb]
        res, mask = [], 0
        for val_num, val in self._values.items():
            if val_num & nb:
                res.append(val)
                mask |= val_num
        if mask != nb:
            res.append(nb ^ mask)
        return (res if res else [nb])

    def _display_value(self, vals):
        res = []
        for val in vals:
            if isinstance(val, scf.Value):
                res.append(val['display_value'])
            else:
                res.append(val)
        return ' | '.join(str(c) for c in res)
