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
    def __str__(self):
        res = 'The current field {name} tried to access to its data, though it'
        res += ' has no data associated with it.'
        return res.format(name='[unkown]')


class FieldNotFoundError(Exception):
    def __init__(self, instance, field, reason=None):
        self.instance, self.field, self.reason = instance, field, reason

    def __str__(self):
        res = 'The field {field} was not found in instance {instance}.\n'
        if self.reason is not None:
            res += 'Reason: {reason}'
        return res.format(instance=self.instance, field=self.field)


class FieldNotReadyError(Exception):
    def __init__(self, field):
        self.field = field

    def __str__(self):
        res = 'The field {field} is not ready. You cannot read its value.'
        return res.format(field=self.field)


class InvalidReferenceError(Exception):
    def __init__(self, ref, reason, **kwds):
        self.ref, self.reason, self.kwds = ref, reason, kwds

    def __str__(self):
        res = 'The value of subfield `{ref}` could\'t be retrieved.\n'
        res += 'Reason: {reason}'
        return res.format(ref=self.ref, reason=self.reason.format(**self.kwds))
