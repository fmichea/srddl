# srddl/fields/containers.py - Container fields.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import copy

from itertools import islice

import srddl.exceptions as se

from srddl.core.fields import AbstractField, BoundValue, reference_value
from srddl.core.offset import Size
from srddl.models import Struct


class AbstractContainerField(AbstractField):
    def encode(self, data, offset, size):
        raise se.ROContainerError()


class SuperFieldBoundValue(BoundValue):
    def __getattr__(self, attr_name):
        return getattr(self.__getitem__('value'), attr_name)

    @property
    def _size(self):
        return self._value['size']


class SuperField(AbstractContainerField):
    '''
    SuperField represents a packed series of fields. It is a sub-division of
    a structure.
    '''

    def __init__(self, cls, *args, **kwargs):
        if not issubclass(cls, Struct):
            raise se.SuperFieldError()
        self._cls = cls
        super().__init__(*args, **kwargs)

    def decode(self, instance, offset):
        return self._cls(instance['data'], offset)

    class Meta:
        boundvalue_class = SuperFieldBoundValue


class ArrayFieldBoundValue(BoundValue):
    def __len__(self):
        return len(self._value)

    def __getitem__(self, idx):
        if isinstance(idx, str):
            res = super().__getitem__(idx)
        elif isinstance(idx, slice):
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

    @property
    def _size(self):
        res = Size()
        for it in self._value:
            res += it.__get__(self._instance)['size']
        return res


class ArrayField(AbstractContainerField):
    def __init__(self, dim, desc, *args, **kwargs):
        self._dim, self._desc = dim, desc
        if not isinstance(desc, AbstractField):
            raise se.ArrayError()
        super().__init__(*args, **kwargs)

    def decode(self, instance, offset):
        data, dim = [], reference_value(instance, self._dim)
        for _ in range(dim):
            desc = copy.copy(self._desc)
            desc.initialize(instance, offset)
            data.append(desc)
            offset += desc.__get__(instance)['size']
        return data

    class Meta:
        boundvalue_class = ArrayFieldBoundValue
