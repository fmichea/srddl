# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import collections
import functools

import srddl.exceptions as se
import srddl.data as sd

from srddl.core.offset import Offset, Size
from srddl.core.fields import AbstractField, FieldInitStatus

class _SrddlInternal:
    '''
    This class is used to create one instance per structure and permit srddl
    to add as much fields as it wants without being too intrusive of the
    structure.
    '''

    def __init__(self, instance, data, offset):
        self.instance, self.data, self.offset = instance, data, Offset(offset)

        # Some meta data on fields.
        self.fields_data = dict()

        # The namespace contains all the fields of the structure.
        self.namespace = collections.OrderedDict()

    def add_namespace(self, namespace):
        for field_name, field in namespace.items():
            if isinstance(field, AbstractField):
                self.namespace[field_name] = field

    def map_struct(self):
        cur_offset = Offset()
        for field_name, field in self.namespace.items():
            field.initialize(self.instance, self.offset + cur_offset)
            cur_offset += field.__get__(self.instance)['size']
        self._size = Size(cur_offset)

    @property
    def fields(self):
        return list(self.namespace.keys())


class _MetaStruct(type):
    '''This MetaStruct is needed for several things:

    - It will ensure that fields of the class are kept in their order.
    - It will also verify that certain constraints on structures are not broken,
    so that algorithms don't have to bother checking afterwards when using them.

    It would be cool to check if we can add __slots__ attribute automatically to
    structures. Indeed a structure souldn't change, and we may create a lot of
    instances.
    '''

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        return collections.OrderedDict()

    def __new__(cls, name, bases, namespace, **kwds):
        kwds = dict(namespace)

        # Wrap init with a function to manage namespaces.
        __init__ = kwds.get('__init__')
        if __init__ is not None:
            @functools.wraps(__init__)
            def init_wrapper(self, *args, **kwargs):
                __init__(self, *args, **kwargs)
                self._srddl.add_namespace(namespace)
        else:
            def init_wrapper(self, *args, **kwargs):
                bases[0].__init__(self, *args, **kwargs)
                self._srddl.add_namespace(namespace)
        kwds['__init__'] = init_wrapper
        return super().__new__(cls, name, bases, kwds)

    def __call__(self, *args, **kwargs):
        res = super().__call__(*args, **kwargs)
        res._srddl.map_struct()
        return res


class Struct(metaclass=_MetaStruct):
    def __init__(self, data, offset):
        if not isinstance(data, sd.Data):
            raise Exception('fuu')
        self._srddl = _SrddlInternal(self, data, offset)

    def __repr__(self):
        args = [self.__class__.__name__, id(self), self['offset']]
        res = '<{} at {:#x} at offset {}\n'.format(*args)
        for field in self['fields']:
            res += '    {} = {},\n'.format(field, getattr(self, field))
        res += '>'
        return res

    def __getitem__(self, item):
        properties = {
            'size': lambda: self._srddl._size,
            'offset': lambda: self._srddl.offset,
            'data': lambda: self._srddl.data
        }
        if item not in properties:
            raise KeyError(item)
        return properties[item]()

    def _setup(self, data):
        '''
        This function permits to map other structures to different part of
        file. When writing a structure, you may want to say that you can map
        some data or other strutures.
        '''
