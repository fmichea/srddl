# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import abc
import collections
import functools
import inspect

import srddl.core.exceptions as sce
import srddl.core.helpers as sch
import srddl.data as sd
import srddl.exceptions as se

import srddl.core.nameddict as zcn

from srddl.core.fields import AbstractMappedValue, AbstractField, FieldInitStatus
from srddl.core.offset import Offset, Size

class _SrddlInternal(AbstractMappedValue):
    '''
    This class is used to create one instance per structure and permit srddl
    to add as much fields as it wants without being too intrusive of the
    structure.
    '''

    class Meta(AbstractMappedValue.Meta):
        init_props = ['_', 'data', 'offset']# + AbstractMappedValue.Meta.init_props

    def __init__(self, instance, data, offset):
        self.instance, self._data, self._offset = instance, data, Offset(offset)

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
        for field_name in self['fields']:
            field = self.namespace[field_name]
            while True:
                field_pi = field.pre_initialize(self.instance)
                if field_pi is None:
                    break
                field, self.namespace[field_name] = field_pi, field_pi
            off = self['offset'] + cur_offset
            field.initialize(self.instance, off, path=field_name)
            cur_offset += field.__get__(self.instance)['size']

    def _size(self, flags):
        size, prop = Size(), 'size' + (':static' if flags['static'] else '')
        for field_name in self['fields']:
            field = self.namespace[field_name]
            try:
                size += field.__get__(self.instance)[prop]
            except TypeError:
                return None
        return size

    @zcn.nameddict_prop()
    def _fields(self, flags):
        lst = list(self.namespace.keys())
        for key, new in self.instance._pre_mapping(self['data'], lst):
            if -1 < new < len(lst):
                del lst[lst.index(key)]
                lst.insert(new, key)
        return lst

    def _hex(self, flags):
        return self._hexify(self._data)

    def _value(self, flags):
        return self._apply_all([], 'value', fn=lambda x: [x])

    def _description(self, flags):
        return inspect.getdoc(self.instance.__class__) or ''

    @zcn.nameddict_abstractprop()
    def _data(self, flags):
        pass

    def _apply_all(self, res, item, fn=lambda x: x):
        for field_name in self._fields:
            res += fn(self.namespace[field_name].__get__(self.instance)[item])
        return res


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
            raise se.NotOnDataError(self)
        self._srddl = _SrddlInternal(self, data, offset)

    def __repr__(self):
        args = [self.__class__.__name__, id(self), self['offset']]
        return '<{} at {:#x} at offset {}>'.format(*args)

    def __str__(self):
        res = repr(self)[:-1] + '\n'
        for field in self['fields']:
            val = str(getattr(self, field)).replace('\n', '\n    ')
            res += '    {} = {},\n'.format(field, val)
        res += '>'
        return res

    def __getitem__(self, item):
        return self._srddl[item]

    def _setup(self, data):
        '''
        This function permits to map other structures to different part of
        file. When writing a structure, you may want to say that you can map
        some data or other strutures.
        '''

    def _pre_mapping(self, data, lst):
        '''
        This function must return a list of modifications done to the order of
        the fields. This modifications will be done in their order. Here is an
        example of the of how it works:

         - Lets say we have the fields ['a', 'b', 'c', 'd'].
         - If you return [('b', 0)], b will be moved to position 0, giving the
           following list: ['b', 'a', 'c', 'd'].
         - If you return [('b', 0), ('c', 3)], b will be moved to position 0,
           and then c will be moved to position 1, giving the following list:
           ['b', 'a', 'd', 'c'].

        By default no modification is done.
        '''
        return []

    def __getattribute__(self, name):
        # Infinite depth recursion fix.
        if name in ['_srddl']:
            return super().__getattribute__(name)
        if name in self._srddl.namespace:
            return self._srddl.namespace[name].__get__(self)
        return super().__getattribute__(name)

    def __setattribute__(self, name, value):
        if name in self._srddl.namespace:
            return self._srddl.namespace[name].__set__(self, value)
        return super().__setattribute__(name, value)


class FileType(sch.MetaConf, metaclass=abc.ABCMeta):
    class MetaBase:
        author_email = ''
        extensions = ''
        version = '[no version]'

    def __init__(self):
        self._attrs = ['name', 'author', 'author_email', 'version', 'abstract',
                       'doc', 'extensions']

    def check(self, data):
        return False

    @abc.abstractmethod
    def setup(self, data):
        pass

    def sanity_check(self, errors_only=False):
        res = ''
        for attr in self._attrs:
            try:
                value = str(self[attr])
                if errors_only:
                    continue
                res += '[OK] "{}" was found with value:'.format(attr)
                if '\n' in value:
                    res += '\n    '
                else:
                    res += ' '
                res += value.replace('\n', '\n    ')
                res += '\n'
            except Exception as e:
                res += '[FAIL] "{}" was not found, with error: {} ({})\n'.format(
                    attr, str(e), e.__class__.__name__
                )
        return res[:-1]

    def __getitem__(self, attr_name):
        if attr_name in self._attrs:
            try:
                return getattr(self, '_{}'.format(attr_name))
            except AttributeError:
                return self.metaconf(attr_name)
        raise KeyError(attr_name)

    @property
    def _extensions(self):
        return list(set(self.metaconf('extensions').split(',')) - set(['']))

    @property
    def _doc(self):
        res = inspect.getdoc(self)
        if res is None:
            raise AttributeError
        return res

    @property
    def _name(self):
        try:
            return self.metaconf('name')
        except sce.NoMetaConfError as e:
            return self.__class__.__name__

    @property
    def _abstract(self):
        try:
            res = self._doc.splitlines()
            if res[0] == '':
                return res[1]
            return res[0]
        except IndexError:
            raise AttributeError
