import pytest

import srddl.data as sd
import srddl.fields as sf
import srddl.models as sm

def test_bitfield_notaligned():
    class Foo(sm.Struct):
        bar1 = sf.BitField(2)
        bar2 = sf.IntField()
    with pytest.raises(Exception):
        foo = Foo(sd.Data(bytes.fromhex('4243')), 0)

def test_bitfield_ok():
    class Foo(sm.Struct):
        bar1 = sf.IntField()
        bar2 = sf.BitField(1)
        bar3 = sf.BitField(1)
        bar4 = sf.BitField(4)
        bar5 = sf.BitField(2)
        bar6 = sf.IntField()
    foo = Foo(sd.Data(bytes.fromhex('43a942')), 0)
    assert(foo.bar1 == 0x43)
    assert(foo.bar2 == 0x1)
    assert(foo.bar3 == 0b0)
    assert(foo.bar4 == 0b1010)
    assert(foo.bar5 == 0b10)
    assert(foo.bar6 == 0x42)

def test_bitfield_ok_1byte():
    class Foo(sm.Struct):
        bar1 = sf.BitField(2)
        bar2 = sf.BitField(4)
        bar3 = sf.BitField(2)
    foo = Foo(sd.Data(bytes.fromhex('a9')), 0)
    assert(foo.bar1 == 0b01)
    assert(foo.bar2 == 0b1010)
    assert(foo.bar3 == 0b10)

def test_bitfield_ok_2bytes():
    class Foo(sm.Struct):
        bar1 = sf.BitField(4)
        pad1 = sf.BitField(9)
        bar2 = sf.BitField(3)
    foo = Foo(sd.Data(bytes.fromhex('affa')), 0)
    assert(foo.bar1 == 0b1111)
    assert(foo.pad1 == 0b110101010)
    assert(foo.bar2 == 0b111)

def test_bitfield_hex():
    class Foo(sm.Struct):
        bar1 = sf.BitField(2)
        bar2 = sf.BitField(4)
        bar3 = sf.BitField(2)
        bar4 = sf.IntField()
    foo = Foo(sd.Data(bytes.fromhex('a942')), 0)
    assert(foo['hex'] == b'a942')
    assert(foo.bar1['hex'] == b'80')
    assert(foo.bar2['hex'] == b'28')
    assert(foo.bar3['hex'] == b'01')
    assert(foo.bar4['hex'] == b'42')
