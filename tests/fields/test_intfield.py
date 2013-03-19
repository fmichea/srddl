import pytest

import srddl.fields as sf
import srddl.models as sm

@pytest.mark.parametrize(('args', 'kwargs', 'buf', 'expected'), [
    ([], dict(), '42', 0x42),
    ([], dict(size=sf.IntField.Size.INT8), '42', 0x42),
    ([], dict(size=sf.IntField.Size.BYTE), '42', 0x42),
    ([], dict(size=sf.IntField.Size.INT16), '4342', 0x4243),
    ([], dict(size=sf.IntField.Size.INT32), '45444342', 0x42434445),
    ([], dict(size=sf.IntField.Size.INT64), '4948474645444342', 0x4243444546474849),

    ([], dict(endianess=sf.IntField.Endianess.LITTLE), '42', 0x42),
    ([], dict(size=sf.IntField.Size.INT8, endianess=sf.IntField.Endianess.LITTLE), '42', 0x42),
    ([], dict(size=sf.IntField.Size.BYTE, endianess=sf.IntField.Endianess.LITTLE), '42', 0x42),
    ([], dict(size=sf.IntField.Size.INT16, endianess=sf.IntField.Endianess.LITTLE), '4342', 0x4243),
    ([], dict(size=sf.IntField.Size.INT32, endianess=sf.IntField.Endianess.LITTLE), '45444342', 0x42434445),
    ([], dict(size=sf.IntField.Size.INT64, endianess=sf.IntField.Endianess.LITTLE), '4948474645444342', 0x4243444546474849),

    ([], dict(endianess=sf.IntField.Endianess.BIG), '42', 0x42),
    ([], dict(size=sf.IntField.Size.INT8, endianess=sf.IntField.Endianess.BIG), '42', 0x42),
    ([], dict(size=sf.IntField.Size.BYTE, endianess=sf.IntField.Endianess.BIG), '42', 0x42),
    ([], dict(size=sf.IntField.Size.INT16, endianess=sf.IntField.Endianess.BIG), '4243', 0x4243),
    ([], dict(size=sf.IntField.Size.INT32, endianess=sf.IntField.Endianess.BIG), '42434445', 0x42434445),
    ([], dict(size=sf.IntField.Size.INT64, endianess=sf.IntField.Endianess.BIG), '4243444546474849', 0x4243444546474849),

    ([], dict(endianess=sf.IntField.Endianess.NETWORK), '42', 0x42),
    ([], dict(size=sf.IntField.Size.INT8, endianess=sf.IntField.Endianess.NETWORK), '42', 0x42),
    ([], dict(size=sf.IntField.Size.BYTE, endianess=sf.IntField.Endianess.NETWORK), '42', 0x42),
    ([], dict(size=sf.IntField.Size.INT16, endianess=sf.IntField.Endianess.NETWORK), '4243', 0x4243),
    ([], dict(size=sf.IntField.Size.INT32, endianess=sf.IntField.Endianess.NETWORK), '42434445', 0x42434445),
    ([], dict(size=sf.IntField.Size.INT64, endianess=sf.IntField.Endianess.NETWORK), '4243444546474849', 0x4243444546474849),

    ([], dict(signed=True), 'be', -0x42),
    ([], dict(size=sf.IntField.Size.INT8, signed=True), 'be', -0x42),
    ([], dict(size=sf.IntField.Size.BYTE, signed=True), 'be', -0x42),
    ([], dict(size=sf.IntField.Size.INT16, signed=True), 'beff', -0x42),
    ([], dict(size=sf.IntField.Size.INT32, signed=True), 'beffffff', -0x42),
    ([], dict(size=sf.IntField.Size.INT64, signed=True), 'beffffffffffffff', -0x42),
])
def test_intfield(args, kwargs, buf, expected):
    class Foo(sm.Struct):
        bar = sf.IntField(*args, **kwargs)
    foo = Foo(bytes.fromhex(buf), 0)
    assert(foo.bar == expected)
    assert(foo.bar['size'] == (len(buf) / 2))
