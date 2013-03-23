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
        bar1 = sf.BitField(2)
        bar2 = sf.BitField(4)
        bar3 = sf.BitField(2)
        bar4 = sf.IntField()
    foo = Foo(sd.Data(bytes.fromhex('a942')), 0)
    assert(foo.bar1 == 0b10)
    assert(foo.bar2 == 0b1010)
    assert(foo.bar3 == 0b01)
    assert(foo.bar4 == 0x42)
