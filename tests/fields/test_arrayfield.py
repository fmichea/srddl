import pytest

import srddl.models as sm
import srddl.fields as sf

@pytest.mark.parametrize(('args', 'kwargs', 'buf'), [
    ([2, sf.IntField()], dict(), '42434445'),
    ([4, sf.IntField()], dict(), '42434445'),
])
def test_arrayfield(args, kwargs, buf):
    class Foo(sm.Struct):
        bar = sf.ArrayField(*args, **kwargs)
    foo = Foo(bytes.fromhex(buf), 0)
    assert(foo.bar['size'] == args[0])
    for it in range(args[0]):
        assert(foo.bar[it] == (0x42 + it))
