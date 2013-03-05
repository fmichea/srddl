# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import abc

import srddl.core.helpers as sch

class _MetaAbstractField(abc.ABCMeta):
    '''
    This metaclass forces some wrappers on the subclasses, so that all instances
    of AbstractFields implement certain features.
    '''

    def __new__(cls, name, bases, namespace, **kwds):
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
        return super().__new__(cls, name, bases, namespace, **kwds)


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
    def size(self, instance):
        '''
        This function must return the size (in bytes) of the current field.
        This function is used along with ``offset`` to find position of all
        fields in the structure and map them correctly.
        '''

    def offset(self, instance):
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
