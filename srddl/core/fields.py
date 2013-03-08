# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import abc
import functools
import inspect
import pprint

import srddl.core.helpers as sch
import srddl.exceptions as se

FieldStatus = sch.enum(KO=0, INIT=1, OK=2)

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
                if self._get_status(instance) != FieldStatus.OK:
                    raise se.FieldNotReadyError(self)
                res = __get__(self, instance, owner=owner)
                from srddl.models import Struct
                if not (res is None or isinstance(res, (BoundValue, Struct))):
                    raise se.NotABoundValueError(self)
                return res
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
            def wrapper(self, instance):
                # There are three states to the initialization process:
                #
                #     FieldStatus.KO -> FieldStatus.INIT -> FieldStatus.OK
                #
                # When the value is not present, this means we haven't even
                # begun to initialize the field. When False, the initialization
                # process has begun, and finally when True everything is fine.
                #
                # Since we want inheritance to work, we need to set the status
                # only on the call on a instance that is the first one.
                status = self._get_status(instance)
                self._set_status(instance, FieldStatus.INIT)
                initialize(self, instance)
                if status == FieldStatus.KO:
                    self._set_status(instance, FieldStatus.OK)
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
        This function must return the decoded value of the field. It should
        always be a BoundValue, though.
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
        return instance._srddl._field_offset(self)

    def _get_data(self, instance):
        '''
        Returns the data associated with the field. This data is stored in
        the special attribute _srddl of the instance, so it is unique for each
        instance. Note that if the data is not initialized, the this function
        will raise .
        '''
        key = id(self)
        if key not in instance._srddl.fields_data:
            raise se.NoFieldDataError()
        return instance._srddl.fields_data[key]

    def _set_data(self, instance, value):
        '''Sets the data associated with the field.'''
        instance._srddl.fields_data[id(self)] = value

    def _field_offset(self, instance, field):
        '''
        Calculates the offset of an inner field, 0 being the beginning of the
        current field. If the field is not a subfield of the current field, it
        must raise FieldNotFoundError. Don't forget to call this function on
        subfields.
        '''
        reason = 'Not a container.'
        raise se.FieldNotFoundError(instance, field, reason)

    def _get_status(self, instance):
        '''
        The status of the field specifies if it is initialized, currently
        initializing or totally not ready, meaning its value is not usable. This
        function is always available and cannot fail.
        '''
        return instance._srddl.fields_status.get(id(self), FieldStatus.KO)

    def _set_status(self, instance, value):
        '''
        This method permits to set the status of the field against a certain
        instance. The value should be a valid value in enum FieldStatus.
        '''
        instance._srddl.fields_status[id(self)] = value

    def _reference_value(self, instance, ref, type_=int):
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
                    instance._srddl._field_offset(ref)
                except se.FieldNotFoundError:
                    reason = 'field is not in structure or not initialized.'
                    raise se.InvalidReferenceError(ref, reason)
                return inner(ref.__get__(instance))
            elif isinstance(ref, BoundValue):
                res = ref.value
                if not isinstance(res, type_):
                    reason = 'BoundValue\'s value is not of the right type.'
                    raise se.InvalidReferenceError(ref, reason)
                return res
            elif inspect.ismethod(ref) or inspect.isfunction(ref):
                return inner(ref(instance))
            reason = 'invalid reference type {type_}, see documentation.'
            raise se.InvalidReferenceError(reason, type_=type(ref))
        return inner(ref)


@functools.total_ordering
class BoundValue(metaclass=_MetaAbstractDescriptor):
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

    def __init__(self, instance, offset, size):
        self._instance, self._size, self._offset = instance, size, offset

    def __getattr__(self, attr_name):
        '''
        Little helper to avoid defining a getter for each public value of the
        class. It also copies public values of the Value class, since they are
        also available properties of a BoundValue.
        '''
        lst = ['size', 'offset'] + Value._fields
        if attr_name not in lst:
            raise AttributeError
        return getattr(self, '_{}'.format(attr_name), None)

    def __repr__(self):
        '''Repesentation of a Bound Value. Really verbose.'''
        pp = pprint.PrettyPrinter(indent=2)
        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        return '<{} at {:#x} with value {}{} for instance {:#x}>'.format(
            class_name, id(self), pp.pformat(self.value),
            ' ({})'.format(self.name) if self.name is not None else '',
            id(self._instance)
        )

    def initialize(self, value):
        '''
        This is the function used to set the value asociated with the
        BoundValue. If a Value is given, it is copied, else the value is
        directly stored with no modification.
        '''
        if isinstance(value, Value):
            for field_name in Value._fields:
                val = getattr(value, field_name)
                setattr(self, '_{}'.format(field_name), val)
        else:
            self._value = value

    def __eq__(self, other):
        # This function is needed by functools.total_ordering.
        if isinstance(other, BoundValue):
            return self.value == other.value
        return self.value == other

    def __lt__(self, other):
        # This function is needed by functools.total_ordering.
        if isinstance(other, BoundValue):
            return self.value < other.value
        return self.value < other


class Value:
    '''
    The Value class is used by the ``values`` keyword parameter of certain
    fields. It is used to define documentation on values possible. The usage
    of this values is dependent on the Field, see their documentation.

    The Value exports the following attributes:
        - value
        - name
        - description
    '''

    _fields = ['value', 'name', 'description']

    def __init__(self, *args, **kwargs):
        for field_name, value in zip(self.__class__._fields, args):
            setattr(self, '_{}'.format(field_name), value)

    def __getattr__(self, attr_name):
        if attr_name not in self.__class__._fields:
            raise AttributeError
        return getattr(self, '_{}'.format(attr_name), None)
