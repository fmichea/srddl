# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import abc
import functools
import pprint

import srddl.core.helpers as sch

class _MetaAbstractDescriptor(abc.ABCMeta):
    '''
    This metaclass inherits from abc.ABCMeta and wrap __get__ and __set__
    functions to implement mandatory instance == None case.
    '''

    def __new__(cls, name, bases, kwds):
        # Wrap __get__ to always implement instance == None case. It also
        # fetches the right instance of struct in case we are in a container.
        __get__ = kwds.get('__get__')
        if __get__ is not None:
            @functools.wraps(__get__)
            def wrapper(self, instance, owner=None):
                if instance is None:
                    return self
                return __get__(self, instance, owner=owner)
            kwds['__get__'] = wrapper

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
    def __new__(cls, clsname, bases, kwds):
        _field_offset = kwds.get('_field_offset')
        if _field_offset is not None:
            @functools.wraps(_field_offset)
            @functools.lru_cache()
            def wrapper(*args, **kwargs):
                return _field_offset(*args, **kwargs)
            kwds['_field_offset'] = wrapper

        initialize = kwds.get('initialize')
        if initialize is not None:
            @functools.wraps(initialize)
            def wrapper(self, instance):
                first = instance._srddl.initialized_fields.get(id(self), None)
                instance._srddl.initialized_fields[id(self)] = False
                initialize(self, instance)
                if first is None:
                    instance._srddl.initialized_fields[id(self)] = True
            kwds['initialize'] = wrapper
        return super().__new__(cls, clsname, bases, kwds)


class AbstractField(metaclass=_MetaAbstractField):
    def initialize(self, instance):
        '''
        This method can be overridden to initialize data against the instance.
        This is mostly used for containers, returning complicated structures.

        You can use helper functions _get_data and _set_data to store data per
        instance. It can then be retrieved in any function.
        '''

    @abc.abstractmethod
    def __get__(self, instance, owner=None):
        '''
        This function must return the decoded value of the field. It can either
        be a integer, a bytearray, a Value or a list of Values.
        '''

    @abc.abstractmethod
    def __set__(self, instance, value):
        '''This function must set the new value of the field.'''

    @abc.abstractmethod
    def _isize(self, instance):
        '''
        This function must return the size (in bytes) of the current field.
        This function is used along with ``offset`` to find position of all
        fields in the structure and map them correctly.
        '''

    def _ioffset(self, instance):
        '''
        This function must return the starting offset of the field. It is a
        wrapper arround ``_field_offset`` called on self.
        '''
        return instance._srddl._field_offset(instance, self)

    def _get_data(self, instance):
        '''Returns the data associated with the field.'''
        return instance._srddl.fields_data[id(self)]

    def _set_data(self, instance, value):
        '''Sets the data associated with the field.'''
        instance._srddl.fields_data[id(self)] = value

    def _field_offset(self, instance, field):
        '''
        Calculates the offset of an inner field, 0 being the beginning of the
        current field. If the field is not a subfield of the current field, it
        must return None. Don't forget to call this function on subfields. By
        default, this function returns ``None``.
        '''
        return None

    def _iinitialized(self, instance, field):
        return instance._srddl.initialized_fields.get(id(field), False)

    def _subfield_value(self, instance, field, type=int):
        if isinstance(field, AbstractField):
            if instance._srddl._field_offset(instance, field) is None:
                raise Exception('fail')
            res = field.__get__(instance).value
            if not isinstance(res, type):
                raise TypeError
            return res
        elif isinstance(field, type):
            return field
        elif inspect.ismethod(field) or inspect.isfunction(field):
            res = field(instance)
            if not isinstance(res, type):
                raise Exception('fail3')
            return res
        raise Exception('fail2')


@functools.total_ordering
class BoundValue(metaclass=_MetaAbstractDescriptor):
    def __init__(self, instance, offset, size):
        '''
        This function initializes the Abstract value with mandatory information
        needed. This is not the function you should override if you want to
        manipulate the value.
        '''
        self._instance, self._size, self._offset = instance, size, offset

    def __getattr__(self, attr_name):
        lst = ['size', 'offset'] + Value._fields
        if attr_name not in lst:
            raise AttributeError
        return getattr(self, '_{}'.format(attr_name), None)

    def __repr__(self):
        pp = pprint.PrettyPrinter(indent=2)
        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        return '<{} at {:#x} with value {}{} for instance {:#x}>'.format(
            class_name, id(self), pp.pformat(self.value),
            ' ({})'.format(self.name) if self.name is not None else '',
            id(self._instance)
        )

    def initialize(self, value):
        if isinstance(value, Value):
            for field_name in Value._fields:
                val = getattr(value, field_name)
                setattr(self, '_{}'.format(field_name), val)
        else:
            self._value = value

    def __eq__(self, other):
        return self.value == other

    def __lt__(self, other):
        return self.value < other


class Value:
    _fields = ['value', 'name', 'description']

    def __init__(self, *args, **kwargs):
        for field_name, value in zip(self.__class__._fields, args):
            setattr(self, '_{}'.format(field_name), value)

    def __getattr__(self, attr_name):
        if attr_name not in self.__class__._fields:
            raise AttributeError
        return getattr(self, '_{}'.format(attr_name), None)
