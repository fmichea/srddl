import pytest

import srddl.models as sm
import srddl.fields as sf


@pytest.mark.parametrize(('args', 'kwargs', 'buf', 'expected'), [
    ([5], dict(), '420000000000', 6),
    ([6], dict(mode=sf.PaddingField.Mode.FILL), '420000000000', 6),
])
def test_paddingfield(args, kwargs, buf, expected):
    class Foo(sm.Struct):
        bar1 = sf.IntField()
        bar2 = sf.PaddingField(*args, **kwargs)
    foo = Foo(bytes.fromhex(buf), 0)
    assert(foo['size'] == expected)
    assert(foo.bar1 == 0x42)
    assert(foo.bar2['size'] == (expected - 1))
