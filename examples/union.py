import srddl.data as sd
import srddl.fields as sf
import srddl.models as sm

class A(sm.Struct):
    a1 = sf.IntField()
    a2 = sf.IntField()

class B(sm.Struct):
    b1 = sf.IntField(size=sf.IntField.Size.INT16)

class Foo(sm.Struct):
    bar = sf.UnionField(a=A, b=B)

foo = Foo(sd.Data(bytes.fromhex('4342')), 0)
assert(foo.bar.a.a1 == 0x43)
assert(foo.bar.a.a2 == 0x42)
assert(foo.bar.b.b1 == 0x4243)
