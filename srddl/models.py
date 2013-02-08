# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

import collections

from srddl.fields import Field, SuperField, Padding

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
        res = type.__new__(cls, name, bases, dict(namespace))
        res.__struct = []
        for key, value in namespace.items():
            if issubclass(value.__class__, (Field, SuperField, Padding)):
                res.__struct.append(key)
        return res

class Struct(metaclass=_MetaStruct): pass
