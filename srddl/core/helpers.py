# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import abc
import functools
import imp
import inspect
import os
import sys

import srddl.core.exceptions as sce

class MetaAbstractDescriptor(abc.ABCMeta):
    '''
    This metaclass inherits from abc.ABCMeta and wrap __get__ and __set__
    functions to implement mandatory instance == None case.
    '''

    def __new__(cls, name, bases, kwds):
        # Wrap __get__ to always implement instance == None case returning the
        # descriptor itself. It also fetches the right instance of struct in
        # case we are in a container.
        __get__ = kwds.get('__get__')
        if __get__ is not None:
            @functools.wraps(__get__)
            def wrapper(self, instance, owner=None):
                if instance is None:
                    return self
                return __get__(self, instance, owner)
            kwds['__get__'] = wrapper

        # The descriptor is not writable on a model level, so it raises an
        # attribute error when set without an instance.
        __set__ = kwds.get('__set__')
        if __set__ is not None:
            @functools.wraps(__set__)
            def wrapper(self, instance, value):
                if instance is None:
                    raise AttributeError("Can't set without an instance.")
                return __set__(self, instance, value)
            kwds['__set__'] = wrapper
        return super().__new__(cls, name, bases, kwds)


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


def class_loader(main_root, cls, func):
    modules = []

    # Finds all the front-ends that can be loaded.
    for root, dirs, files in os.walk(main_root):
        for filename in files:
            if not filename.endswith('.py'):
                continue
            mod_name = root[len(main_root):].replace('/', '.') + filename[:-3]
            try:
                tmp = [root] + sys.path
                modules.append((mod_name, imp.find_module(mod_name, tmp)))
            except ImportError:
                pass

    modules = sorted(modules, key=lambda mod: mod[0])
    for mod_name, (fd, pathname, description) in modules:
        try:
            mod = imp.load_module(mod_name, fd, pathname, description)
            for item in inspect.getmembers(mod):
                if inspect.isclass(item[1]) and issubclass(item[1], cls):
                    func(item[1])
        except ImportError:
            pass
