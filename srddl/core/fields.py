# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import abc
import functools
import inspect
import pprint

import srddl.core.helpers as sch
import srddl.exceptions as se

from srddl.core.signals import Signal
from srddl.core.offset import Offset, Size

FieldInitStatus = sch.enum(KO=0, INIT=1, OK=2)

REFERENCE_SIGNAL = Signal('current-ref')

class _MetaAbstractDescriptor(abc.ABCMeta):
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


class _MetaAbstractField(_MetaAbstractDescriptor):
    '''
    This meta-class will make sure that initialization of a Field is done
    correctly.
    '''

    def __new__(cls, clsname, bases, kwds):
        # When referencing a field from another, we basically need to know if
        # the field is initialized or not, so if we can fetch its value or not.
        initialize = kwds.get('initialize')
        if initialize is not None:
            @functools.wraps(initialize)
            def wrapper(self, instance, offset):
                # There are three states to the initialization process:
                #
                #   FieldInitStatus.KO, FieldInitStatus.INIT, FieldInitStatus.OK
                #
                # When the value is not present, this means we haven't even
                # begun to initialize the field. When False, the initialization
                # process has begun, and finally when True everything is fine.
                #
                # Since we want inheritance to work, we need to set the status
                # only on the call on a instance that is the first one.
                try:
                    status = self._get_data(instance, 'status')
                except se.NoFieldDataError:
                    status = FieldInitStatus.KO
                self._set_data(instance, 'status', FieldInitStatus.INIT)
                initialize(self, instance, offset)
                if status != FieldInitStatus.INIT:
                    self._set_data(instance, 'status', FieldInitStatus.OK)
            kwds['initialize'] = wrapper

        __get__ = kwds.get('__get__')
        if __get__ is not None:
            @functools.wraps(__get__)
            @functools.lru_cache()
            def wrapper(self, instance, owner=None):
                if self._get_data(instance, 'status') != FieldInitStatus.OK:
                    raise se.FieldNotReadyError(self)
                res = __get__(self, instance, owner=owner)
                from srddl.models import Struct
                if not (res is None or isinstance(res, (BoundValue, Struct))):
                    raise se.NotABoundValueError(self)
                return res
            kwds['__get__'] = wrapper

        for func_name in ['decode']:
            func = kwds.get(func_name)
            if func is not None:
                @functools.wraps(func)
                @functools.lru_cache()
                def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)
                kwds[func_name] = wrapper
        return super().__new__(cls, clsname, bases, kwds)

def reference_value(instance, ref, type_=int):
    '''
    This function permits to retrieve the value of a Field, a lambda or a
    BoundValue until it is valid with ``type`` (``int`` by default). If it
    is none of theses types, it raises InvalidReferenceError. It may also
    raise FieldNotReady if the lambda/function fetches an uninitialized
    field.
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

class FindMeAName:
    fields = []

    def __init__(self, *args, **kwargs):
        '''
        Init function of this class has a specific behavior. Positional
        arguments are are in the order of the ``fields`` list. Then you can
        override specific values with keyword arguments.
        '''
        vals = dict(zip(self.__class__.fields, args))
        vals.update(kwargs)
        for name in self.__class__.fields:
            if name not in vals:
                continue
            setattr(self, '_{}'.format(name), vals.get(name, None))

    def __getitem__(self, attr_name):
        '''This function permits to access the attributes of the object.'''
        if attr_name not in self.__class__.fields:
            raise AttributeError
        return getattr(self, '_{}'.format(attr_name), None)

    def copy(self, other):
        for field in type(other).fields:
            setattr(self, '_{}'.format(field), other[field])


class Value(FindMeAName):
    '''
    The Value class is used by the ``values`` keyword parameter of certain
    fields. It is used to define documentation on values possible. The usage
    of this values is dependent on the Field, see their documentation.

    The Value exports the following attributes:
        - value
        - name
        - description
    '''

    fields = ['value', 'name', 'description']

    def __repr__(self):
        res = '<Value at {:#x} with value {}'.format(id(self), self['value'])
        if self['name'] is not None:
            res += ' ({})'.format(self['name'])
        res += '>'
        return res


@functools.total_ordering
class BoundValue(Value, metaclass=_MetaAbstractDescriptor):
    '''
    The BoundValue class represents a value obtained by fetching a Field. Each
    field may define and return a specialized version of the BoundValue,
    defining properties for more advanced usage of these values.

    If a Value was found, it is copied over the BoundValue, so you can retreive
    the documentation associated with the Value (during Field definition)
    directly with the BoundValue.

    Aside from this, the BoundValue also exposes the size of the value (in
    bytes) and its offset. You may not need these value, but they are public
    anyway.
    '''

    fields = ['offset', 'size'] + Value.fields

    def __init__(self, instance, field, offset):
        super().__init__(offset)
        self._field, self._instance = field, instance

    def __repr__(self):
        res = '<{} at {:#x}'.format(self.__class__.__name__, id(self))
        if self['value'] is not None:
            value = repr(self['value']).replace('\n', '\n    ')
            res += ' with value {}'.format(value)
            if self['name'] is not None:
                res += ' ({})'.format(self['name'])
        res += '>'
        return res

    def __getitem__(self, item):
        if item != 'value' and item in Value.fields:
            # Force decoding of value for those fields.
            _ = self._value
        return super().__getitem__(item)

    @property
    def _size(self):
        return Size(byte=reference_value(self._instance, self._field._size))

    @property
    def _value(self):
        res = self._field.decode(self._instance, self._offset)
        if isinstance(res, Value):
            self.copy(res)
            return res['value']
        return res

    @_value.setter
    def _value(self, value):
        pass

    def __bool__(self):
        return bool(self._value)

    def __eq__(self, other):
        # This function is needed by functools.total_ordering.
        if isinstance(other, BoundValue):
            return self._value == other._value
        return self._value == other

    def __lt__(self, other):
        # This function is needed by functools.total_ordering.
        if isinstance(other, BoundValue):
            return self.value < other.value
        return self.value < other


class AbstractField(FindMeAName, metaclass=_MetaAbstractField):
    fields = ['description']

    class _MetaBase:
        aligned = True
        boundvalue_class = BoundValue

    def initialize(self, instance, offset):
        if self._metaconf_value('aligned') and not offset.aligned():
            raise Exception('bit alignment not respected.')
        bv = self._metaconf_value('boundvalue_class')(instance, self, offset)
        self._set_data(instance, 'boundvalue', bv)
        return bv['size']

    @functools.lru_cache()
    def __get__(self, instance, owner=None):
        return self._get_data(instance, 'boundvalue')

    def __set__(self, instance, value):
        '''This function must set the new value of the field.'''
        bv = self.__get__(instance)
        offset = instance['offset'] + bv['offset']
        self.encode(instance, offset, value)

    @abc.abstractmethod
    def decode(self, instance, offset):
        pass

    @abc.abstractmethod
    def encode(self, instance, offset, value):
        pass

    def _data_key(self, name):
        return 'data-{:x}_{}'.format(id(self), name)

    def _get_data(self, instance, name):
        key = self._data_key(name)
        if key not in instance._srddl.fields_data:
            raise se.NoFieldDataError(instance, self, name)
        return instance._srddl.fields_data[key]

    def _set_data(self, instance, name, value):
        '''Sets the data associated with the field.'''
        instance._srddl.fields_data[self._data_key(name)] = value

    def _metaconf_value(self, key):
        try:
            return getattr(getattr(self, 'Meta'), key)
        except AttributeError:
            return getattr(self.__class__._MetaBase, key)
