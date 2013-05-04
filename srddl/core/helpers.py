# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import inspect

import srddl.core.exceptions as sce

def enum(**enums):
    if 'values' in enums:
        raise ValueError('Can\'t create enum with "values" value name. Sorry.')
    namespace = enums.copy()
    namespace['values'] = lambda: enums.values()
    namespace['keys'] = lambda: enums.keys()
    namespace['items'] = lambda: enums.items()
    return type('Enum', (), namespace)


def reference_value(instance, ref, type_=int):
    from srddl.core.fields import AbstractField, BoundValue
    '''
    This function permits to retrieve the value of a Field, a lambda or a
    BoundValue until it is valid with ``type`` (``int`` by default). If it is
    none of theses types, it raises InvalidReferenceError. It may also raise
    FieldNotReady if the lambda/function fetches an uninitialized field.
    '''
    def inner(ref):
        if isinstance(ref, type_):
            # Dereference finally gave a good value, so we return it
            # directly.
            return ref
        elif isinstance(ref, AbstractField):
            try:
                #instance._srddl._field_offset(ref)
                pass
            except se.FieldNotFoundError:
                reason = 'field is not in structure or not initialized.'
                raise se.InvalidReferenceError(ref, reason)
            return inner(ref.__get__(instance))
        elif isinstance(ref, BoundValue):
            res = ref['value']
            if not isinstance(res, type_):
                reason = 'BoundValue\'s value is not of the right type.'
                raise se.InvalidReferenceError(ref, reason)
            return res
        elif inspect.ismethod(ref) or inspect.isfunction(ref):
            return inner(ref(instance))
        reason = 'invalid reference type {type_}, see documentation.'
        raise se.InvalidReferenceError(reason, type_=type(ref))
    return inner(ref)


class MetaConf:
    class MetaBase:
        pass

    @classmethod
    def metaconf(cls, key):
        for meta in ['Meta', 'MetaBase']:
            try:
                return getattr(getattr(cls, meta), key)
            except AttributeError:
                pass
        raise sce.NoMetaConfError(cls, key)


class NamedDict(MetaConf):
    class MetaBase:
        fields = []
        ro_fields = []

    def __init__(self, *args, **kwargs):
        '''
        Init function of this class has a specific behavior. Positional
        arguments are are in the order of the ``fields`` list. Then you can
        override specific values with keyword arguments.
        '''
        vals = dict(zip(self.metaconf('fields'), args))
        vals.update(kwargs)
        for name in self.metaconf('fields'):
            if name not in vals:
                continue
            setattr(self, '_{}'.format(name), vals.get(name, None))

    def __getitem__(self, attr_name):
        '''This function permits to access the attributes of the object.'''
        lst = self.metaconf('fields') + self.metaconf('ro_fields')
        if attr_name not in lst:
            raise KeyError
        try:
            return getattr(self, '_{}'.format(attr_name), None)
        except AttributeError:
            raise KeyError

    def __setitem__(self, attr_name, value):
        if attr_name not in self.metaconf('fields'):
            raise KeyError
        setattr(self, '_{}'.format(attr_name), value)

    def copy(self, other):
        for field in type(other).metaconf('fields'):
            setattr(self, '_{}'.format(field), other[field])


class NamedRecord(MetaConf):
    class MetaBase:
        fields = []

    def __init__(self, *args, **kwargs):
        vals = dict(zip(self.metaconf('fields'), args))
        vals.update(kwargs)
        for name in self.metaconf('fields'):
            if name not in vals:
                continue
            setattr(self, '_{}'.format(name), vals.get(name, None))

    def __getattr__(self, attr_name):
        if attr_name in self.metaconf('fields'):
            return getattr(self, '_{}'.format(attr_name), None)
        raise AttributeError(attr_name)

    def __setattr__(self, attr_name, value):
        if attr_name in self.metaconf('fields'):
            return setattr(self, '_{}'.format(attr_name), value)
        return super().__setattr__(attr_name, value)

    def copy(self, other):
        for field in other.metaconf('fields'):
            setattr(self, '_{}'.format(field), getattr(other, field))
