import pytest

from srddl.core.offset import _Offset


@pytest.mark.parametrize(('a', 'b', 'c'), [
    (_Offset(), _Offset(), _Offset()),
    (_Offset(bit=2), _Offset(), _Offset(bit=2)),
    (_Offset(), _Offset(bit=2), _Offset(bit=2)),
    (_Offset(byte=1, bit=2), _Offset(byte=2, bit=3), _Offset(byte=3, bit=5)),
    (_Offset(byte=1, bit=7), _Offset(bit=1), _Offset(byte=2)),
    (_Offset(byte=1, bit=5), _Offset(byte=1, bit=4), _Offset(byte=3, bit=1)),
    (_Offset(), 1, _Offset(byte=1)),
])
def test_add_offset(a, b, c):
    assert((a + b) == c)


@pytest.mark.parametrize(('a', 'b', 'c'), [
    (_Offset(), _Offset(), _Offset()),
    (_Offset(byte=2), _Offset(), _Offset(byte=2)),
    (_Offset(byte=3), 2, _Offset(byte=1)),
    (_Offset(byte=3), _Offset(byte=2), _Offset(byte=1)),
    (_Offset(bit=2), _Offset(), _Offset(bit=2)),
    (_Offset(bit=3), _Offset(bit=2), _Offset(bit=1)),
    (_Offset(byte=1, bit=2), _Offset(byte=0, bit=3), _Offset(byte=0, bit=7)),
])
def test_sub_offset(a, b, c):
    assert((a - b) == c)
