# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

class NotAFieldError(Exception):
    def __init__(self, struct, field):
        self._struct, self._field = struct, field

    def __str__(self):
        return 'The given field {!r} is not a field of {!r}'.format(
            self._field, self._struct
        )


class SuperFieldError(Exception):
    def __str__(self):
        return 'A SuperField must take a structure class as a parameter.'


class ArrayError(Exception):
    def __str__(self):
        return 'The array content must be a field.'


class ROContainerError(Exception):
    def __str__(self):
        res = 'Containers are read-only, you can set their content but not'
        res += ' them directly.'
        return res


class NoFieldDataError(Exception):
    def __init__(self, struct, field, item):
        self.struct, self.field, self.item = struct, field, item

    def __str__(self):
        res = 'A field of type {field} in struct {struct} tried to access to'
        res += ' its data "{item}", although it has no data with this name.'
        return res.format(field=self.field.__class__.__name__, item=self.item,
                          struct=self.struct.__class__.__name__)


class FieldNotReadyError(Exception):
    def __init__(self, field):
        self.field = field

    def __str__(self):
        res = 'The field {field} is not ready. You cannot read its value.'
        return res.format(field=self.field.__class__.__name__)


class InvalidReferenceError(Exception):
    def __init__(self, ref, reason, **kwds):
        self.ref, self.reason, self.kwds = ref, reason, kwds

    def __str__(self):
        res = 'The value of field "{ref}" could\'t be retrieved.\n'
        res += 'Reason: {reason}'
        return res.format(ref=self.ref, reason=self.reason.format(**self.kwds))


class NotABoundValueError(Exception):
    def __init__(self, field):
        self.field = field

    def __str__(self):
        res = 'The value returned by {field} was not a BoundValue.'
        return res.format(field=self.field)

# ----- Fields Exceptions ------------------------------------------------------

class BifFieldSizeError(Exception):
    def __init__(self, size):
        self.size = size

    def __str__(self):
        return 'The size {size} is not suitable for a BitField.'.format(
            size = self.size
        )


# ----- Struct Exceptions ------------------------------------------------------

class NotOnDataError(Exception):
    def __init__(self, struct):
        self.struct = struct

    def __str__(self):
        return 'Struct {struct_name} was called on a non-data instance.'.format(
            struct_name = self.struct.__class__.__name__,
        )


# ----- Signal Exceptions ------------------------------------------------------

class SignalExistsError(Exception):
    def __init__(self, signame):
        self.signame = signame

    def __str__(self):
        return 'Tried to create signal "{signame}" that already exists.'.format(
            self.signame
        )


class SignalNotFoundError(Exception):
    def __init__(self, signame, action):
        self.signame, self.action = signame, action

    def __str__(self):
        return 'The signal "{signame}" was not found while {action}.'.format(
            signame=self.signame, action=self.action
        )


class SignalHandlerNotFoundError(Exception):
    def __init__(self, signame, idx):
        self.signame, self.idx = signame, idx

    def __str__(self):
        res = 'Signal handler {idx:#x} was not found for signal "{signame}".'
        return res.format(signame=self.signame, idx=self.idx)


class SignalHandlerCallError(Exception):
    def __init__(self, signame, func):
        self.signame, self.func = signame, func

    def __str__(self):
        res = 'Signal handler {func} call was not successful for signal '
        res += '"{signame}". Check backtrace.'
        return res.format(func=self.func, signame=self.signame)


# ----- Data Exceptions --------------------------------------------------------

class NoMappedDataError(Exception):
    def __init__(self, offset):
        self.offset = offset

    def __str__(self):
        res = 'There is no struture mapped at offset {offset}.'
        return res.format(offset=self.offset)


class DataIsROError(Exception):
    def __init__(self, data, offset):
        self.data, self.offset = data, offset

    def __str__(self):
        res = 'Data {data} is read-only, can\'t set its content at offset'
        res += ' {offset}.'
        return res.format(data=self.data, offset=self.offset)
