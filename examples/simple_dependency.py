import srddl.models as sm
import srddl.fields as sf

buf = bytearray.fromhex('0242434445')

class Foo(sm.Struct):
    length = sf.IntField()
    data = sf.ArrayField(length, sf.IntField())

f = Foo(buf, 0)

assert(f.length == 2)
assert(f.data == [0x42, 0x43])

f.length = 4

assert(f.data == [0x42, 0x43, 0x44, 0x45])
