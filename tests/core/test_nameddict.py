import pytest

import srddl.core.exceptions as sce
import srddl.core.nameddict as scnd

class A(scnd.NamedDict):
    @scnd.property(flags=['f1', 'f2'])
    def _prop1(self, flags):
        if flags['f1'] and flags['f2']: return 0
        if flags['f1']: return 1
        if flags['f2']: return 2
        return 3

class B(A):
    def _prop1(self, flags):
        pass

class C(A):
    @scnd.abstractproperty()
    def _prop2(self, flags):
        pass

class D(C):
    def _prop2(self, flags):
        pass

class E(C):
    def _prop2(self, flags):
        return True

class F(C):
    class Meta:
        init_props = ['prop2']

    def __init__(self, prop2):
        self._prop2 = prop2

@pytest.mark.parametrize(('attr', 'val'), [
    ('prop1', 3),
    ('prop1:f1', 1),
    ('prop1:f2', 2),
    ('prop1:f1,f2', 0),
])
def test_property_get(attr, val):
    a = A()
    assert(a[attr] == val)

def test_unknown_property():
    a = A()
    with pytest.raises(KeyError):
        a['unknwon_prop']

def test_unknown_propflag():
    a = A()
    with pytest.raises(sce.NamedDictPropertyFlagsError):
        a['prop1:funknown']

def test_simple_override():
    b = B()
    assert(b['prop1'] is None)

def test_abstract_instanciation():
    with pytest.raises(sce.NamedDictAbstractPropertyError):
        c = C()

@pytest.mark.parametrize(('klass', 'val'), [
    (D, None),
    (E, True),
])
def test_abstract_success(klass, val):
    i = klass()
    assert(i['prop2'] == val)

@pytest.mark.parametrize(('val',), [(1,), (2,), (3,)])
def test_abstract_success_constructor(val):
    f = F(val)
    assert(f['prop2'] is val)

def test_override_with_flags_error():
    with pytest.raises(sce.NamedDictPropertyRedefinitionError):
        class Failure(A):
            @scnd.property(flags=['oops'])
            def _prop1(self, flags):
                pass

def test_override_to_abstract_error():
    with pytest.raises(sce.NamedDictPropertyRedefinitionError):
        class Failure(A):
            @scnd.abstractproperty()
            def _prop1(self, flags):
                pass

def test_override_cant_copy():
    with pytest.raises(sce.NamedDictPropertyRedefinitionError):
        class Failure(C):
            @property
            def _prop1(self):
                pass
