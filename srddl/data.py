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
        self.view = DataView(self)

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


class DataView:
    PAGE_SIZE = 16
    COLUMN_SIZE = 16

    def __init__(self, data):
        self._data, self._offset, self._sline = data, 0, 0

    def __call__(self, lines):
        # Move _sline arround if needed.
        if self._sline is None:
            self._sline = self.line - lines // 2
            self._sline = max(0, min(self._sline, self.line - lines))
        elif self.line < self._sline:
            self._sline = self.line
        elif self._sline + lines <= self.line:
            self._sline = self.line - lines + 1

        # Fetch data and return it.
        column = DataView.COLUMN_SIZE
        offset = self._sline * column
        size = min(lines * column, len(self._data) - offset)
        data = self._data.unpack_from('{}B'.format(size), offset)
        return collections.OrderedDict(zip(
            (offset + it * column for it in range(lines)),
            zip(*([iter(data)] * column))
        ))

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
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
