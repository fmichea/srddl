import srddl.data as sd
import srddl.fields as sf
import srddl.models as sm

class A(sm.Struct):
    a = sf.IntField()
    b = sf.SwitchField(a, {
        0: sf.IntField(size=sf.IntField.Size.INT32),
        1: sf.ByteArrayField(4),
    })

data = sd.Data(bytearray.fromhex('0045444342'))

a = A(data, 0)

assert(a.a == 0)
assert(a.b == 0x42434445)

data.pack_into('B', 0, 1)

a = A(data, 0)

assert(a.a == 1)
assert(a.b == bytes.fromhex('45444342'))
