# srddl/core/exceptions.py - Exceptions used only in core modules.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

# ----- Helpers ----------------------------------------------------------------

class NoMetaConfError(Exception):
    '''
    This exception is raised when a Meta configuration is not found for a
    class. Metaconf are used as variables configuring the behavior of a
    subclass of an abstract class.

    :param klass: The class on which the metaconf function was called.
    :param name: The name of the configuration value requested.
    '''

    def __init__(self, klass, name):
        self.klass, self.name = klass, name

    def __str__(self):
        res = 'Configuration for "{name}" key was not found for class {klss}.'
        return res.format(name = self.name, klss = self.klass.__name__)


# ----- NamedDict Exceptions ---------------------------------------------------

class NamedDictAbstractPropertyError(Exception):
    '''
    This exception is raised when an instance of a sub-class of a
    NamedDict is created but this class still has abstract properties. A
    NamedDict must have all its properties implemented or set by the
    constructor of the class.

    Those checks are done even before the method ``__init__`` of the
    class is called.

    :param klass: The class which instance was requested.
    :param props: The name of the abstract properties unimplemented.
    :param reason: The reason why the property is still considered
                   abstract.
    '''

    def __init__(self, klass, props, reason):
        self.klass, self.props, self.reason = klass, props, reason

    def __str__(self):
        res = 'Can\'t instanciate class {klass}. Propert'
        res += ('ies' if 1 < len(self.props) else 'y') + ' {props} w'
        res += ('ere' if 1 < len(self.props) else 'as') + ' not implemented:'
        res += ' {reason}'
        return res.format(klass=self.klass, props=', '.join(self.props), reason=self.reason)


class NamedDictPropertyFlagsError(Exception):
    '''
    This error means that a property was requested with a flag that is
    not known. For properties' flags, the strictness was choosen since
    flags are just part of the string, so a typo is easy to do.

    :param klass: The class on which the property was requested.
    :param propname: The name of the property that was requested.
    :param flags: A list of flags that are not known to the property.
    '''

    def __init__(self, klass, propname, flags):
        self.klass, self.propname, self.flags = klass, propname, flags

    def __str__(self):
        flags = ', '.join(self.flags)
        res = 'Can\'t fetch value for property {propname} in class {klass}. '
        res += 'Flag' + ('s ' if 1 < len(self.flags) else '') + ' {flags} '
        res += ('are' if 1 < len(self.flags) else 'is') + ' not known.'
        return res.format(klass=self.klass, propname=self.propname, flags=flags)


class NamedDictPropertyRedefinitionError(Exception):
    '''
    There are certain cases where a property can't be defined again. You
    can't, for instance, define a property as abstract when it was
    already implemented in one of the parents of the class. The reason
    given should give you a real insgiht into what went wrong.

    :param klass: The class in which the property is defined again.
    :param propname: The name of the redefined property.
    :param reason: The reason why the redefinition failed.
    '''

    def __init__(self, klass, propname, reason):
        self.klass, self.propname, self.reason = klass, propname, reason

    def __str__(self):
        res = 'Can\'t redefine property {propname} in class {klass}: {reason}'
        return res.format(propname=self.propname, klass=self.klass, reason=self.reason)


# ----- File types loader ------------------------------------------------------

class FileTypeNameError(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'At least two file types share the name {name}.'.format(
            name = self.name
        )
