import srddl.models as sm
import srddl.fields as sf

class B(sm.Struct):
    b_first = sf.Field(size=sf.Field_Sizes.INT32)

class A(sm.Struct):
    a_first = sf.Field('First field')
    a_second = sf.Field('Second field', size=sf.Field_Sizes.INT32,
                        endianess=sf.Field_Endianess.BIG)
    a_third = sf.SuperField(B)
    a_fourth = sf.Array(4, sf.Field())
    a_fifth = sf.ByteArrayField('Fifth field', size=10)
    a_sixth = sf.Padding(2)
    a_seventh = sf.Field(size=sf.Field_Sizes.INT16)
    a_pad = sf.Padding(33, mode=sf.PaddingMode.FILL)
    a_eigth = sf.Field(values=[sf.Value(0x4, 'VALUE')])

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
assert(a.size() == 34)
assert(a.a_eigth == 4)
print('Eigth:', repr(a.a_eigth))

#print('data:', data)
#a.a_first = 0x01
#assert(a.a_first == 0x1)
#print('data:', data)
#a.a_fourth[1] = 0x66
#assert(a.a_fourth[1] == 0x66)
#print('data:', data)
#a.a_fourth[1:3] = [0x66, 0x60]
#print('data:', data)
#a.a_second = 0x08048832ff
#print('data:', data)
#a.a_second = 0
#print('data:', data)
#a.a_second = -1
#print('data:', data)
