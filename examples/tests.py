import srddl.data as sd
import srddl.fields as sf
import srddl.models as sm

class A(sm.Struct):
    a = sf.IntField()
    b = sf.IntField()

class B(A):
    b = sf.ByteArrayField(4)
    c = sf.IntField()

b = B(sd.Data(bytes.fromhex('424344454647')), 0)

# b has fields ['a', 'b', 'c'] with b field being a ByteArrayField.
