# srddl/helpers.py - Some helper functions to help writing templates.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

'''Some helper functions to help writing templates.'''

def invalid(val):
    '''Always says the value is invalid.'''
    return False

def equals(expected):
    def _equals(value):
        return value == bytearray(expected)
    return _equals
