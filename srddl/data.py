import collections
import mmap
import math
import os
import struct
import string

import srddl.core.helpers as sch
import srddl.exceptions as se

from srddl.core.fields import BoundValue
from srddl.core.offset import Offset

class Data:
    class MappedData(dict):
        def __getitem__(self, key):
            if isinstance(key, tuple):
                offset, fltr = key
            else:
                offset, fltr = key, None
            offset = Offset(offset)
            res = super().__getitem__(offset)
            res = [x for x in res if fltr is None or fltr(x)]
            if len(res) == 1:
                return res[0]
            raise se.NoMappedDataError(offset)

        def keys(self):
            for offset in sorted(super().keys()):
                if len(super().__getitem__(offset)) == 1:
                    # XXX: Should we yield with a None filter to make fetching
                    #      of offsets easier? (not two cases to manage)
                    yield offset
                else:
                    for s in self[offset]:
                        yield (offset, lambda t: t is s)

        def values(self):
            for _, item in self.items():
                yield item

        def items(self):
            for key in self.keys():
                yield (key, self.__getitem__(key))

    def __init__(self, buf, ro=False):
        self.buf, self.ro, self.mapped = buf, ro, Data.MappedData()

        # Probably not foolproof...
        try: self.buf[0] = self.buf[0]
        except: self.ro = True

    def __del__(self):
        self.close()

    def __len__(self):
        return len(self.buf)

    def map(self, offset, struct):
        offset = Offset(offset)
        s = struct(self, offset)
        self.mapped[offset] = self.mapped.get(offset, []) + [s]
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


class DataView:
    PAGE_SIZE = 16
    COLUMN_SIZE = 8

    def __init__(self, data, columns=2):
        self._data, self._offset, self._columns = data, 0, columns

    def __call__(self, line, lines, display=True):
        # Fetch data and return it.
        column = DataView.COLUMN_SIZE * self._columns
        offset = line * column
        size = min(lines * column, len(self._data) - offset)
        data = self._data.unpack_from('{}B'.format(size), offset)
        data  = zip(*([iter(data)] * column))
        tmpres = collections.OrderedDict(zip(
            (offset + it * column for it in range(lines)),
            [list(zip(*([iter(d)] * DataView.COLUMN_SIZE))) for d in data]
        ))
        if not display:
            return tmpres
        addr_width, res = len(hex(len(self._data))), collections.OrderedDict()

        printable = set(string.printable) - set('\a\b\f\n\r\t\v')
        strings = lambda b: chr(b) if chr(b) in printable else None
        for addr, data in tmpres.items():
            res['{addr:#0{aw}x}'.format(addr=addr, aw=addr_width)] = {
                'data': [['{:02x}'.format(b) for b in d] for d in data],
                'strings': [[strings(b) for b in d] for d in data],
            }
        return res

    @property
    def offset(self):
        return self._offset

    def set_offset(self, value):
        self._offset = max(min(len(self._data), value), 0)

    @property
    def line(self):
        return self._offset // DataView.COLUMN_SIZE

    @property
    def column(self):
        return self._offset % DataView.COLUMN_SIZE

    def up(self):
        if self._offset < DataView.COLUMN_SIZE:
            return
        self._offset -= DataView.COLUMN_SIZE

    def right(self):
        if self._offset == len(self._data) - 1:
            return
        self._offset += 1

    def left(self):
        if self._offset == 0:
            return
        self._offset -= 1

    def down(self):
        l = len(self._data)
        if l - l % DataView.COLUMN_SIZE < self._offset:
            return
        self._offset += DataView.COLUMN_SIZE
        if l <= self._offset:
            self._offset = l - 1

    def pageup(self):
        for _ in range(DataView.PAGE_SIZE):
            self.up()

    def pagedown(self):
        for _ in range(DataView.PAGE_SIZE):
            self.down()

    def max_lines(self):
        return math.ceil(len(self._data) / (DataView.COLUMN_SIZE * self._columns))


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
