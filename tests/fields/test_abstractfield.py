import pytest

import srddl.data as sd
import srddl.exceptions as se
import srddl.fields as sf
import srddl.models as sm

data = sd.Data(bytearray(b'\x42ZIZI\x43'))

class A(sm.Struct):
    a = sf.IntField()
    b = sf.AbstractField()
    c = sf.IntField()

class B(A):
    b = sf.IntField(size=sf.IntField.Size.INT32)

class C(A):
    b = sf.ByteArrayField(4)

def test_raise_abstractstruct():
    with pytest.raises(se.AbstractStructError):
        a = A(data, 0)

def test_ok_b():
    b = B(data, 0)
    assert(b.a == 0x42)
    assert(b.b == 0x495a495a)
    assert(b.c == 0x43)

def test_ok_c():
    c = C(data, 0)
    assert(c.a == 0x42)
    assert(c.b == bytes(b'ZIZI'))
    assert(c.c == 0x43)
