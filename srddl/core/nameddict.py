# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import srddl.core.exceptions as sce
import srddl.core.helpers as sch

def _nameddict_propname(funcname):
    return funcname[1:]  # XXX: Assumes that the func is private (starts with _).

class _MetaNamedDict(sch.MetaAbstractDescriptor):
    def __new__(cls, clsname, bases, namespace, **kwds):
        res = super().__new__(cls, clsname, bases, namespace, **kwds)

        props, aprops = set(), set()
        for base in bases:
            try:
                props.update(base.__nd_props__)
                aprops.update(base.__nd_abstractprops__)
            except AttributeError:
                pass
        for kwd_name, kwd_val in res.__dict__.items():
            try:
                propname = _nameddict_propname(kwd_name)
                if propname in aprops:
                    try:
                        reason = None
                        if kwd_val.__nd_propabstract__:
                            reason = 'you can\'t add an implementation as '
                            reason += 'abstract.'
                        if kwd_val.__nd_propflags__ != []:
                            reason = 'you can\'t change flags in a '
                            reason += 'sub-implementation.'
                        if reason is not None:
                            raise sce.NamedDictPropertyRedefinitionError(
                                res.__name__, propname, reason
                            )
                    except AttributeError:
                        attr = getattr(super(res, res), kwd_name)
                        _nameddict_prop.copy(kwd_val, attr)
                    aprops.discard(propname)
                elif propname in props and not hasattr(kwd_val, '__nd_propabstract__'):
                    attr = getattr(super(res, res), kwd_name)
                    _nameddict_prop.copy(kwd_val, attr)
                p = props
                if kwd_val.__nd_propabstract__:
                    p = aprops
                p.add(kwd_val.__nd_propname__)
            except AttributeError:
                pass
        res.__nd_props__ = props
        res.__nd_abstractprops__ = aprops
        return res

    def __call__(self, *args, **kwargs):
        abstracts = self.__nd_abstractprops__ - set(self.metaconf('init_props'))
        if abstracts:
            reason = 'propert' + ('ies are' if len(abstracts) else 'y is')
            reason += ' not defined.'
            raise sce.NamedDictAbstractPropertyError(self.__name__, abstracts, reason)

        # Checks that the abstract properties supposed to be set by init really
        # are.
        abstracts, count = [], 0
        for name in self.metaconf('init_props'):
            count += 1
            if name == '_': # Skip parameters not for NamedDict.
                continue
            if name not in self.__nd_abstractprops__:
                continue
            if name in kwargs:
                continue
            if len(args) < count:
                abstracts.append(name)
        if abstracts:
            reason = 'property is not set by the constructor of the class'
            reason += ' (not enough arguments)'
            raise sce.NamedDictAbstractPropertyError(self, abstracts, reason)
        return super().__call__(*args, **kwargs)


# FIXME: Add the possibility to set properties (with a read-only possibility).
class _nameddict_prop:
    def __init__(self, abstract, flags=None):
        self.abstract, self.flags = abstract, flags

    def __call__(self, func):
        func.__nd_propabstract__ = self.abstract
        func.__nd_propname__ = _nameddict_propname(func.__name__)
        func.__nd_propflags__ = self.flags or []
        return func

    @staticmethod
    def copy(a, b):
        fields = ['name', 'flags']
        for f in fields:
            f = '__nd_prop{}__'.format(f)
            setattr(a, f, getattr(b, f))
        a.__nd_propabstract__ = False

class nameddict_prop(_nameddict_prop):
    def __init__(self, *args, **kwargs):
        super().__init__(False, *args, **kwargs)

class nameddict_abstractprop(_nameddict_prop):
    def __init__(self, *args, **kwargs):
        super().__init__(True, *args, **kwargs)

_NAMEDDICT_SEP = ':'
_NAMEDDICT_FSEP = ','

class NamedDict(sch.MetaConf, metaclass=_MetaNamedDict):
    class MetaBase:
        init_props = []

    def __init__(self, *args, **kwargs):
        '''
        Init function of this class has a specific behavior. Positional
        arguments are are in the order of the ``fields`` list. Then you can
        override specific values with keyword arguments.
        '''
        vals = dict(zip([c for c in self.metaconf('init_props') if c != '_'], args))
        vals.update(kwargs)
        for name in self.metaconf('init_props'):
            if name not in vals:
                continue
            try:
                prop = getattr(self, '_{}'.format(name))
                if prop.__nd_propabstract__:
                    raise AttributeError('OK')
            except AttributeError:
                setattr(self, '_{}'.format(name), vals.get(name, None))

    def __getitem__(self, _attr_name):
        '''This function permits to access the attributes of the object.'''
        try:
            attr_name, attr_flags = _attr_name.split(_NAMEDDICT_SEP, 1)
        except ValueError:
            attr_name, attr_flags = _attr_name, ''
        init_props = set(self.__class__.__nd_abstractprops__)
        init_props &= set(self.metaconf('init_props'))
        init_props |= self.__class__.__nd_props__
        if attr_name not in init_props:
            raise KeyError
        prop = getattr(self, '_{}'.format(attr_name))

        attr_flags = [f.strip() for f in attr_flags.split(_NAMEDDICT_FSEP)]
        while True:
            try: attr_flags.remove('')
            except ValueError: break
        try:
            funknown = set(attr_flags) - set(prop.__nd_propflags__)
        except AttributeError:
            return prop
        if funknown:
            args = [self.__class__.__name__, attr_name, funknown]
            raise sce.NamedDictPropertyFlagsError(*args)
        kwds = dict([(c, False) for c in prop.__nd_propflags__])
        kwds.update(dict([(c, True) for c in attr_flags]))
        return prop(kwds)

    def copy(self, other):
        for field in type(other).__nd_props__:
            setattr(self, '_{}'.format(field), other[field])
