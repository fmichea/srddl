import pytest

import srddl.data as sd
import srddl.fields as sf
import srddl.models as sm

@pytest.mark.parametrize(('args', 'kwargs', 'buf', 'expected'), [
    ([4], dict(), '42434445', '42434445'),
    ([4], dict(), '4243444546474849', '42434445'),
])
def test_bytearrayfield(args, kwargs, buf, expected):
    expected = bytes.fromhex(expected)
    class Foo(sm.Struct):
        bar = sf.ByteArrayField(*args, **kwargs)
    foo = Foo(sd.Data(bytes.fromhex(buf)), 0)
    assert(foo.bar == expected)
    assert(foo.bar['size'] == len(expected))
