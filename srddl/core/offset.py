# srddl/core/offset.py - Helps describe offsets and sizes.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import functools

@functools.total_ordering
class _Offset:
    def __init__(self, byte=0, bit=0):
        from srddl.core.fields import BoundValue
        if isinstance(byte, BoundValue):
            self.byte, self.bit = byte['value'], bit
        elif isinstance(byte, _Offset):
            self.byte, self.bit = byte.byte, byte.bit
        else:
            self.byte, self.bit = byte, bit

    def __repr__(self):
        return '<{} at {:#x} with value ({}, {})>'.format(
            self.__class__.__name__, id(self), self.byte, self.bit
        )

    def __hash__(self):
        return hash('{}::{}'.format(self.byte, self.bit))

    def __eq__(self, other):
        # This function is needed by functools.total_ordering.
        if isinstance(other, _Offset):
            return (self.byte, self.bit) == (other.byte, other.bit)
        return (self.byte, self.bit) == (other, 0)

    def __lt__(self, other):
        # This function is needed by functools.total_ordering.
        if isinstance(other, _Offset):
            return (self.byte, self.bit) < (other.byte, other.bit)
        return (self.byte, self.bit) < (other, 0)

    def __add__(self, other):
        if isinstance(other, _Offset):
            bit = self.bit + other.bit
            byte = self.byte + other.byte + (bit >> 3)
            bit &= 0b111
            return self.__class__(byte=byte, bit=bit)
        return self.__class__(byte=(self.byte + other), bit=self.bit)

    def __sub__(self, other):
        if isinstance(other, _Offset):
            bit = self.bit - other.bit
            byte = self.byte + other.byte
            if bit < 0:
                bit = 8 - bit
                byte -= 1
            return self.__class__(byte=byte, bit=bit)
        return self.__class__(byte=(self.byte - other), bit=self.bit)

    def __rsub__(self, other):
        return self.__class__(byte=(other - self.byte), bit=self.bit)

    def aligned(self):
        return (self.bit == 0)


class Offset(_Offset): pass
class Size(_Offset): pass
