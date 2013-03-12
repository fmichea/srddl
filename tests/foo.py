import srddl.models as sm
import srddl.fields as sf

class B(sm.Struct):
    b_first = sf.IntField(size=sf.Field_Sizes.INT32)

class A(sm.Struct):
    a_first = sf.IntField('First field')
    a_second = sf.IntField('Second field', size=sf.Field_Sizes.INT32,
                        endianess=sf.Field_Endianess.BIG)
    a_third = sf.SuperField(B)
    a_fourth = sf.Array(4, sf.IntField())
    a_fifth = sf.ByteArrayField(10, 'Fifth field')
    a_sixth = sf.Padding(2)
    a_seventh = sf.IntField(size=sf.Field_Sizes.INT16)
    a_pad = sf.Padding(33, mode=sf.PaddingMode.FILL)
    a_eigth = sf.IntField(values=[sf.Value(0x4, 'VALUE')])

class C(sm.Struct):
    length = sf.IntField()
    data = sf.Array(length, sf.IntField())

class D(sm.Struct):
    length = sf.IntField()
    data = sf.Array(lambda struct: 2, sf.IntField())

class E(sm.Struct):
    data = sf.Array(lambda struct: struct.length, sf.IntField())
    length = sf.IntField()

data = '2adeadbeefefbeadde424344450001020304050607080900002a2b00000000000004'
data = bytearray.fromhex(data)

a = A(data, 0)

assert(a.a_first == 0x2a)
assert(a.a_second == 0xdeadbeef)
assert(a.a_third.b_first == 0xdeadbeef)

for i in range(4):
    assert(a.a_fourth[i] == (0x42 + i))

assert(a.a_fifth == bytearray.fromhex('00010203040506070809'))
assert(a.a_seventh == 0x2b2a)
assert(a.size == 34)
assert(a.a_eigth == 4)

data = bytearray.fromhex('0242434445')

c = C(data, 0)

assert(c.length == 2)
assert(c.data == [0x42, 0x43])

d = D(data, 0)

assert(d.length == 2)
assert(d.data == [0x42, 0x43])

try:
    e = E(data, 0)
    assert(False)
except Exception:
    pass # OK, SHOULD RAISE

class F(sm.Struct):
    b = sf.SuperField(B)
    data = sf.Array(lambda struct: struct.b.b_first, sf.IntField())

data = bytearray.fromhex('020000004243')

f = F(data, 0)

assert(f.b.b_first == 2)
assert(f.data == [0x42, 0x43])
