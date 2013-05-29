import pytest

from srddl.core.offset import (_Offset as _OffsetBase, Offset, Size)

class _Offset(_OffsetBase):
    def rounded(self):
        raise Exception('Don\'t do that.')

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

@pytest.mark.parametrize(('obj', 'res'), [
    (Offset(), 0),
    (Offset(bit=3), 0),
    (Offset(bit=7), 0),
    (Offset(byte=1), 1),
    (Offset(byte=1, bit=3), 1),
    (Size(), 0),
    (Size(bit=3), 1),
    (Size(bit=7), 1),
    (Size(byte=1), 1),
    (Size(byte=1, bit=3), 2),
])
def test_rounded(obj, res):
    assert(obj.rounded() == res)
