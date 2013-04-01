# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import inspect

def enum(**enums):
    if 'values' in enums:
        raise ValueError('Can\'t create enum with "values" value name. Sorry.')
    namespace = enums.copy()
    namespace['values'] = lambda: enums.values()
    namespace['keys'] = lambda: enums.keys()
    namespace['items'] = lambda: enums.items()
    return type('Enum', (), namespace)


def reference_value(instance, ref, type_=int):
    from srddl.core.fields import AbstractField, BoundValue
    '''
    This function permits to retrieve the value of a Field, a lambda or a
    BoundValue until it is valid with ``type`` (``int`` by default). If it is
    none of theses types, it raises InvalidReferenceError. It may also raise
    FieldNotReady if the lambda/function fetches an uninitialized field.
    '''
    def inner(ref):
        if isinstance(ref, type_):
            # Dereference finally gave a good value, so we return it
            # directly.
            return ref
        elif isinstance(ref, AbstractField):
            try:
                #instance._srddl._field_offset(ref)
                pass
            except se.FieldNotFoundError:
                reason = 'field is not in structure or not initialized.'
                raise se.InvalidReferenceError(ref, reason)
            return inner(ref.__get__(instance))
        elif isinstance(ref, BoundValue):
            res = ref['value']
            if not isinstance(res, type_):
                reason = 'BoundValue\'s value is not of the right type.'
                raise se.InvalidReferenceError(ref, reason)
            return res
        elif inspect.ismethod(ref) or inspect.isfunction(ref):
            return inner(ref(instance))
        reason = 'invalid reference type {type_}, see documentation.'
        raise se.InvalidReferenceError(reason, type_=type(ref))
    return inner(ref)
