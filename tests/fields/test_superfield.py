import pytest

import srddl.models as sm
import srddl.fields as sf


class A(sm.Struct):
    a1 = sf.IntField()
    a2 = sf.IntField()


class B(sm.Struct):
    b1 = sf.IntField()
    b2 = sf.IntField()
    b3 = sf.IntField()


@pytest.mark.parametrize(('args', 'kwargs', 'buf', 'expected', 'size'), [
    ([A], dict(), '42434445', dict(a1=0x42, a2=0x43), 2),
    ([B], dict(), '424344', dict(b1=0x42, b2=0x43, b3=0x44), 3),
])
def test_superfield(args, kwargs, buf, expected, size):
    class Foo(sm.Struct):
        bar = sf.SuperField(*args, **kwargs)
    foo = Foo(bytes.fromhex(buf), 0)
    assert(foo.bar['size'] == size)
    for attr, value in expected.items():
        assert(getattr(foo.bar, attr, None), value)
