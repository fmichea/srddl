# srddl/fields/containers.py - Container fields.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import copy

from itertools import islice

import srddl.exceptions as se

from srddl.core.fields import AbstractField, BoundValue
from srddl.models import Struct

class AbstractContainerField(AbstractField):
    def __get__(self, instance, owner=None):
        return self._get_data(instance)

    def __set__(self, instance, value):
        raise se.ROContainerError()

    def _isize(self, instance):
        return self._get_data(instance).size

class SuperField(AbstractContainerField):
    '''
    SuperField represents a packed series of fields. It is a sub-division of
    a structure.
    '''

    def __init__(self, cls):
        if not issubclass(cls, Struct):
            raise se.SuperFieldError()
        self._cls = cls

    def initialize(self, instance):
        self._set_data(instance, self._cls(instance.buf, self._ioffset(instance)))

    def _field_offset(self, instance, field):
        struct = self._get_data(instance)
        if field is struct:
            return 0
        return struct._srddl._field_offset(field)


class Array(AbstractContainerField):
    class _ArrayInner(BoundValue):
        def __len__(self):
            return len(self._value)

        def __getitem__(self, idx):
            if isinstance(idx, slice):
                res = []
                for it in islice(self._value, idx.start, idx.stop, idx.step):
                    res.append(it.__get__(self._instance))
            else:
                res = self._value[idx].__get__(self._instance)
            return res

        def __setitem__(self, idx, value):
            if isinstance(idx, slice):
                tmp = zip(islice(self._value, idx.start, idx.stop, idx.step), value)
                for it, value in tmp:
                    it.__set__(self._instance, value)
            else:
                self._value[idx].__set__(self._instance, value)

        def __iter__(self):
            for it in self._value:
                yield it.__get__(self._instance)

        def _field_offset(self, instance, field):
            res = instance._srddl._field_offset(field, fields=tuple(self._value))
            return (self._offset + res)

        @property
        def size(self):
            return sum(it.__get__(self._instance).size for it in self._value)

        @property
        def value(self):
            return list(iter(self))


    def __init__(self, dim, desc):
        self._dim, self._desc = dim, desc
        if not isinstance(desc, AbstractField):
            raise se.ArrayError()

    def initialize(self, instance):
        data, dim = [], self._reference_value(instance, self._dim)
        for _ in range(dim):
            tmp = copy.copy(self._desc)
            tmp.initialize(instance)
            data.append(tmp)
        res = Array._ArrayInner(instance, self._ioffset(instance), None)
        res.initialize(data)
        self._set_data(instance, res)

    def _field_offset(self, instance, field):
        return self._get_data(instance)._field_offset(instance, field)
