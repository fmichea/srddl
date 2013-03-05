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
