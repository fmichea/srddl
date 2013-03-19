# PYTHONPATH="." python -i tests/ndh/steg200.py ~/ctf/ndh/2013/steg200/stream

import sys

import srddl.data as sd
import srddl.fields as sf
import srddl.models as sm

class UnknownChunk(sm.Struct):
    pad = sf.PaddingField(1)
    length = sf.IntField(size=sf.IntField.Size.INT32)
    data = sf.ByteArrayField(length)

class UnknownFile(sm.Struct):
    pad = sf.PaddingField(1)
    length = sf.IntField(size=sf.IntField.Size.INT32)
    chunks = sf.ArrayField(length, sf.SuperField(UnknownChunk))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage: {} streamFile.bin')

    with sd.FileData(sys.argv[1]) as data:
        s = UnknownFile(data, 0)
