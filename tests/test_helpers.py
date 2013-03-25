import pytest

import srddl.helpers as sh

@pytest.mark.parametrize(('a', 'b', 'res'), [
    (1, 1, True),
    (1, 2, False),
])
def test_equals(a, b, res):
    assert(sh.equals(a)(b) is res)

some_values = [(True,), (False,), (1,), (0,), (None,)]

@pytest.mark.parametrize(('a'), some_values)
def test_valid(a):
    assert(sh.valid(a))

@pytest.mark.parametrize(('a'), some_values)
def test_invalid(a):
    assert(not sh.invalid(a))
