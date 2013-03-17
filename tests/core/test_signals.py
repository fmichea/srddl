import pytest

import srddl.core.signals as scs
import srddl.exceptions as se

TEST_SIGNAL = 'test-signal'

@pytest.fixture
def signal():
    s = scs.Signal()
    s.create(TEST_SIGNAL)
    return s

def test_create():
    signal = scs.Signal()
    name = TEST_SIGNAL + '-creation'
    assert(name not in signal.signals())
    signal.create(name)
    assert(name in signal.signals())

def test_signals_list(signal):
    assert(TEST_SIGNAL in signal.signals())

def test_double_creation(signal):
    with pytest.raises(se.SignalExistsError):
        signal.create(TEST_SIGNAL)

def test_subscribe_and_trigger(signal):
    foo = []
    def handler():
        foo.append(1)
    signal.subscribe(TEST_SIGNAL, handler)
    signal.trigger(TEST_SIGNAL)
    assert(len(foo) != 0)

def test_trigger_bad_call(signal):
    def handler(lala):
        pass
    signal.subscribe(TEST_SIGNAL, handler)
    with pytest.raises(se.SignalHandlerCallError):
        signal.trigger(TEST_SIGNAL)

def test_unsubscribe(signal):
    foo = []
    def handler():
        foo.append(1)
    pk = signal.subscribe(TEST_SIGNAL, handler)
    signal.trigger(TEST_SIGNAL)
    assert(len(foo) == 1)
    signal.unsubscribe(TEST_SIGNAL, pk)
    signal.trigger(TEST_SIGNAL)
    assert(len(foo) == 1)

def test_bad_unsubscribe(signal):
    with pytest.raises(se.SignalHandlerNotFoundError):
        signal.unsubscribe(TEST_SIGNAL, 0)

def test_subscribe_unknwon_signal(signal):
    with pytest.raises(se.SignalNotFoundError):
        signal.subscribe(TEST_SIGNAL + '-unknown', lambda: 0)

def test_unsubscribe_unknwon_signal(signal):
    with pytest.raises(se.SignalNotFoundError):
        signal.unsubscribe(TEST_SIGNAL + '-unknown', 0)

def test_trigger_unknwon_signal(signal):
    with pytest.raises(se.SignalNotFoundError):
        signal.trigger(TEST_SIGNAL + '-unknown')
