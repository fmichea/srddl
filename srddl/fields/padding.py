from srddl.fields import Field

def enum(**enums):
    return type('Enum', (), enums)

PaddingMode = enum(TAKE=0, FILL=1)

class Padding(Field): pass
