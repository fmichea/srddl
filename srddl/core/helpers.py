# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

def enum(**enums):
    if 'values' in enums:
        raise ValueError('Can\'t create enum with "values" value name. Sorry.')
    namespace = enums.copy()
    namespace['values'] = lambda: enums.values()
    namespace['keys'] = lambda: enums.keys()
    namespace['items'] = lambda: enums.items()
    return type('Enum', (), namespace)
