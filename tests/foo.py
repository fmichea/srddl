import srddl.models as sm
import srddl.fields as sf

class B(sm.Struct):
    b_first = sf.Field(size=sf.Field_Sizes.INT32)

class A(sm.Struct):
    a_first = sf.Field()
    a_second = sf.Field(size=sf.Field_Sizes.INT32,
                        endianess=sf.Field_Endianess.BIG)
    a_third = sf.SuperField(B)
    a_fourth = sf.Array(4, sf.Field())

data = bytearray(bytes.fromhex('2adeadbeefefbeadde42434445'))

a = A(data, 0)

assert(a.a_first == 0x2a)
assert(a.a_second == 0xdeadbeef)
assert(a.a_third.b_first == 0xdeadbeef)

for i in range(4):
    assert(a.a_fourth[i] == (0x42 + i))

print('data:', data)
a.a_first = 0x01
assert(a.a_first == 0x1)
print('data:', data)
a.a_fourth[1] = 0x66
assert(a.a_fourth[1] == 0x66)
print('data:', data)
a.a_fourth[1:3] = [0x66, 0x60]
print('data:', data)
a.a_second = 0x08048832ff
print('data:', data)
a.a_second = 0
print('data:', data)
a.a_second = -1
print('data:', data)
