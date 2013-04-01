import collections
import mmap
import os
import struct

import srddl.core.helpers as sch
import srddl.exceptions as se

from srddl.core.fields import BoundValue
from srddl.core.offset import Offset

class Data:
    def __init__(self, buf, ro=False):
        self.buf, self.ro, self._mapped = buf, ro, dict()

        # Probably not foolproof...
        try: self.buf[0] = self.buf[0]
        except: self.ro = True

    def __del__(self):
        self.close()

    def __len__(self):
        return len(self.buf)

    def mapped(self, offset, fltr=None):
        offset = Offset(offset)
        res = [x for x in self._mapped[offset] if fltr is None or fltr(x)]
        if len(res) == 1:
            return res[0]
        raise se.NoMappedDataError(offset)

    def map(self, offset, struct):
        offset = Offset(offset)
        s = struct(self, offset)
        self._mapped[offset] = self._mapped.get(offset, []) + [s]
        s._setup(self)
        return s

    def map_array(self, offset, nb, struct):
        offset = Offset(offset)
        for _ in range(nb):
            offset += self.map(offset, struct)['size']

    def unpack_from(self, frmt, offset):
        return struct.unpack_from(frmt, self.buf, offset)

    def pack_into(self, frmt, offset, *args):
        if self.ro:
            raise se.DataIsROError(self, offset)
        struct.pack_into(frmt, self.buf, offset, *args)

    def close(self):
        pass

    def view(self, line, lines):
        column = 16
        if line % column != 0:
            Exception('Wrong!')
        data = self.unpack_from('{}B'.format(column * lines), column * line)
        return collections.OrderedDict(zip(
            ((line + it) * column for it in range(lines)),
            zip(*([iter(data)] * column))
        ))


class FileData(Data):
    Mode = sch.enum(
        RDONLY=('rb', mmap.PROT_READ),
        RDWR=('r+b', mmap.PROT_READ | mmap.PROT_WRITE),
    )

    def __init__(self, filename, mode=Mode.RDONLY):
        self.f, self.filename = open(filename, mode[0]), filename
        super().__init__(mmap.mmap(self.f.fileno(), 0, prot=mode[1]))

    def __len__(self):
        return os.path.getsize(self.filename)

    def close(self):
        self.buf.close()
        self.f.close()
