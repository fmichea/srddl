# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import abc
import functools
import inspect
import pprint

import srddl.core.helpers as sch
import srddl.exceptions as se
import srddl.helpers as sh

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
            def wrapper(self, instance, offset, **kwargs):
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
                initialize(self, instance, offset, **kwargs)
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


class Value(sch.NamedDict):
    '''
    The Value class is used by the ``values`` keyword parameter of certain
    fields. It is used to define documentation on values possible. The usage
    of this values is dependent on the Field, see their documentation.

    The Value exports the following attributes:
        - value
        - name
        - description
    '''

    class Meta:
        fields = ['value', 'name', 'description']
        ro_fields = ['display_value']

    def __repr__(self):
        return '<Value at {:#x} with value {}>'.format(
            id(self), self['value']
        )

    @property
    def _display_value(self):
        res = str(self['value'])
        if self['name'] is not None:
            res += ' ({})'.format(self['name'])
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

    class Meta:
        fields = ['offset'] + Value.Meta.fields
        ro_fields = ['field', 'size', 'value'] + Value.Meta.ro_fields

    def __init__(self, instance, field, offset, valid):
        super().__init__(offset)
        self._field, self._instance, self._valid_func = field, instance, valid

    def __repr__(self):
        res = '<{} at {:#x}'.format(self.__class__.__name__, id(self))
        value = self['value']
        if value is not None:
            res += ' with value {}'.format(value)
        res += '>'
        return res

    def __str__(self):
        return '{} {}>'.format(
            ' '.join(repr(self).split()[:5]), self['display_value']
        )

    def __getitem__(self, item):
        if item != 'value' and item in Value.metaconf('fields'):
            # Force decoding of value for those fields.
            _ = self._value
        return super().__getitem__(item)

    @property
    def _size(self):
        return Size(byte=sch.reference_value(self._instance, self._field._size))

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

    @property
    def _valid(self):
        return self._valid_func(self._value)

    @property
    def _display_value(self):
        res = self._field._display_value(self._value)
        if res is None and self['value'] is not None:
            if self['name'] is not None:
                res = super()._display_value
            else:
                res = str(self['value']).replace('\n', '\n    ')
        return res

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


class AbstractField(sch.NamedDict, metaclass=_MetaAbstractField):
    class MetaBase(sch.NamedDict.MetaBase):
        aligned = True
        boundvalue_class = BoundValue

        fields = ['description']
        ro_fields = ['path']

    def __init__(self, *args, **kwargs):
        self._valid = kwargs.pop('valid', lambda _: None)
        super().__init__(*args, **kwargs)

    def pre_initialize(self, instance):
        return None

    def initialize(self, instance, offset, path=None):
        if self.metaconf('aligned') and not offset.aligned():
            raise Exception('bit alignment not respected.')
        args = [instance, self, offset, self._valid]
        bv = self.metaconf('boundvalue_class')(*args)
        if path is not None:
            self._path = path
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

    def _display_value(self, val):
        return None
