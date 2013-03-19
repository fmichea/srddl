import mmap
import struct

import srddl.core.helpers as sch

class Data:
    def __init__(self, buf, ro=False):
        self.buf, self.ro = buf, ro

        # Probably not foolproof...
        try: self.buf[0] = self.buf[0]
        except: self.ro = True

    def pack_into(self, frmt, offset, *args):
        if self.ro:
            raise Exception('fu')
        struct.pack_into(frmt, self.buf, offset, *args)

    def unpack_from(self, frmt, offset):
        return struct.unpack_from(frmt, self.buf, offset)


class FileData(Data):
    Mode = sch.enum(
        RDONLY=('rb', mmap.PROT_READ),
        RDWR=('r+b', mmap.PROT_READ | mmap.PROT_WRITE),
    )

    def __init__(self, filename, mode=Mode.RDONLY):
        self.f = open(filename, mode[0])
        super().__init__(mmap.mmap(self.f.fileno(), 0, prot=mode[1]))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.buf.close()
        self.f.close()
