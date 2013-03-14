import srddl.models as sm
import srddl.fields as sf

class Foo(sm.Struct):
    length = sf.IntField()
    data = sf.Array(length, sf.Array(length, sf.IntField()))

f = Foo(bytearray.fromhex('0242434445'), 0)

#assert(f.length == 2)
#assert(f.data == [0x42, 0x43]))
