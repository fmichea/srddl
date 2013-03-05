# srddl/fields/containers.py - Container fields.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import copy

from itertools import islice

import srddl.exceptions as se

from srddl.core.abstract import AbstractField
from srddl.models import Struct

class AbstractContainerField(AbstractField):
    def __get__(self, instance, owner=None):
        return self._get_data(instance)

    def __set__(self, instance, value):
        raise se.ROContainerError()

    def size(self, instance):
        return self._get_data(instance).size()


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
        self._set_data(instance, self._cls(instance.buf, self.offset(instance)))

    def _field_offset(self, instance, field):
        if field is self._get_data(instance):
            return 0
        return self._get_data(instance)._srddl._field_offset(instance, field)


class Array(AbstractContainerField):
    class _Inner:
        def __init__(self, instance, data):
            self.instance, self.data = instance, data

        def __repr__(self):
            return '<{} at {} containing {} for instance {}>'.format(
                repr(self.__class__)[8:-2], hex(id(self)),
                list(self), self.instance
            )

        def __len__(self):
            return len(self.data)

        def __getitem__(self, idx):
            if isinstance(idx, slice):
                res = []
                for it in islice(self.data, idx.start, idx.stop, idx.step):
                    res.append(it.__get__(self.instance))
            else:
                res = self.data[idx].__get__(self.instance)
            return res

        def __setitem__(self, idx, value):
            if isinstance(idx, slice):
                tmp = zip(islice(self.data, idx.start, idx.stop, idx.step), value)
                for it, value in tmp:
                    it.__set__(self.instance, value)
            else:
                self.data[idx].__set__(self.instance, value)

        def __iter__(self):
            for it in self.data:
                yield it.__get__(self.instance)

        def _field_offset(self, instance, field):
            offset = 0
            for it in self.data:
                if it is field:
                    return offset
                tmp = it._field_offset(instance, field)
                if tmp is not None:
                    return offset + tmp
                offset += it.size(instance)
            return None

        def size(self):
            return sum(it.size(self.instance) for it in self.data)


    def __init__(self, dim, desc):
        self._dim, self._desc = dim, desc
        if not isinstance(desc, AbstractField):
            raise se.ArrayError()

    def initialize(self, instance):
        res = []
        for _ in range(self._dim):
            tmp = copy.copy(self._desc)
            tmp.initialize(instance)
            res.append(tmp)
        self._set_data(instance, Array._Inner(instance, res))

    def _field_offset(self, instance, field):
        return self._get_data(instance)._field_offset(instance, field)
