# srddl/helpers.py - Some helper functions to help writing templates.
# Author: Franck Michea < franck.michea@gmail.com >
# License: New BSD License (See LICENSE)

'''Some helper functions to help writing templates.'''

def invalid(val):
    '''Value is alwaus considered invalid.'''
    return False

def valid(val):
    '''Value is always considered valid.'''
    return True

def equals(expected):
    '''Checks that the value matches the expected value.'''
    def _equals(value):
        return value == bytearray(expected)
    return _equals
