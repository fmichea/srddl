# srddl/fields/containers.py - Container fields.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import copy

from itertools import islice

import srddl.core.fields as scf
import srddl.core.helpers as sch
import srddl.core.offset as sco
import srddl.exceptions as se
import srddl.models as sm


class AbstractContainerField(scf.AbstractField):
    def encode(self, data, offset, size):
        raise se.ROContainerError()


class SuperFieldBoundValue(scf.BoundValue):
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
        if not issubclass(cls, sm.Struct):
            raise se.SuperFieldError()
        self._cls = cls
        super().__init__(*args, **kwargs)

    def decode(self, instance, offset):
        return self._cls(instance['data'], offset)

    class Meta:
        boundvalue_class = SuperFieldBoundValue


class ArrayFieldBoundValue(scf.BoundValue):
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
        res = sco.Size()
        for it in self._value:
            res += it.__get__(self._instance)['size']
        return res


class ArrayField(AbstractContainerField):
    def __init__(self, dim, desc, *args, **kwargs):
        self._dim, self._desc = dim, desc
        if not isinstance(desc, scf.AbstractField):
            raise se.ArrayError()
        super().__init__(*args, **kwargs)

    def decode(self, instance, offset):
        data, dim = [], sch.reference_value(instance, self._dim)
        for _ in range(dim):
            desc = copy.copy(self._desc)
            desc.initialize(instance, offset)
            data.append(desc)
            offset += desc.__get__(instance)['size']
        return data

    class Meta:
        boundvalue_class = ArrayFieldBoundValue


class UnionFieldBoundValue(scf.BoundValue):
    def __getattr__(self, attr_name):
        if attr_name not in self._value:
            raise AttributeError
        return self._value[attr_name]

    @property
    def _size(self):
        return self._value[list(self._value.keys())[0]]['size']


class UnionField(AbstractContainerField):
    def __init__(self, *args, **kwargs):
        self.substructs, items = dict(), list(kwargs.items())
        for name, struct in items:
            if issubclass(struct, Struct):
                self.substructs[name] = kwargs.pop(name)
        if len(self.substructs) < 2:
            raise se.UnionFieldCountError()
        super().__init__(*args, **kwargs)

    def decode(self, instance, offset):
        res, size = dict(), None
        for name, struct in self.substructs.items():
            res[name] = struct(instance['data'], offset)
            if size is None:
                size = res[name]['size']
            if res[name]['size'] != size:
                raise se.UnionFieldSizeError()
        return res

    class Meta:
        boundvalue_class = UnionFieldBoundValue
