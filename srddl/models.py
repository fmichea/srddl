# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import collections
import functools

from srddl.core.fields import AbstractField

class _SrddlInternal:
    '''
    This class is used to create one instance per structure and permit srddl
    to add as much fields as it wants without being too intrusive of the
    structure.
    '''

    def __init__(self, instance, namespace):
        self.instance = instance
        self.fields = list()
        self.fields_data = dict()
        self.initialized_fields = dict()
        self.namespace = collections.OrderedDict()
        self.add_namespace(namespace)

    def add_namespace(self, namespace):
        for field_name, field in namespace.items():
            if isinstance(field, AbstractField):
                self.fields.append(field_name)
                self.namespace[field_name] = field
                field.initialize(self.instance)

    def _isize(self, instance):
        res = 0
        for field_name, field_desc in self.namespace.items():
            res += field_desc.__get__(instance).size
        return res

    @functools.lru_cache()
    def _field_offset(self, instance, field):
        offset = self.instance.offset
        for field_name, field_desc in self.namespace.items():
            if field_desc is field:
                return offset
            # This protects the referencing of other fields that are not
            # initialized yet, during initialization of one field.
            if not self._iinitialized(field_desc):
                return None
            tmp = field_desc._field_offset(self.instance, field)
            if tmp is not None:
                return offset + tmp
            offset += field_desc.__get__(self.instance).size
        return None

    def _iinitialized(self, field):
        return self.initialized_fields.get(id(field), False)


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

        # Wrap init with a function to treat correctly containers.
        __init__ = kwds.get('__init__')
        if __init__ is not None:
            @functools.wraps(__init__)
            def init_wrapper(self, *args, **kwargs):
                __init__(self, *args, **kwargs)
                if not hasattr(self, '_srddl'):
                    self._srddl = _SrddlInternal(self, namespace)
                else:
                    self._srddl.add_namespace(namespace)
        else:
            def init_wrapper(self, *args, **kwargs):
                try:
                    super(self.__class__, self).__init__(*args, **kwargs)
                    self._srddl.add_namespace(namespace)
                except AttributeError:
                    self._srddl = _SrddlInternal(self, namespace)
        kwds['__init__'] = init_wrapper
        return super().__new__(cls, name, bases, kwds)

class Struct(metaclass=_MetaStruct):
    def __init__(self, buf, offset):
        self.buf, self.offset = buf, offset

    @property
    def size(self):
        return self._srddl._isize(self)
