# fe_common.py - Common logic shared with all frontends.

import srddl.core.helpers as sch

class HexViewColors:
    # BOTH_ENDS = BEGIN and END
    pos = sch.enum(BEGIN=0, MIDDLE=1, END=2, BOTH_ENDS=3)

    def __init__(self):
        self.ocolors = dict()

    def color(self, offset):
        def _sub(offset, level=None):
            if offset not in self.ocolors:
                return (-1, None)
            if level is None:
                level = max(self.ocolors[offset].keys())
            elif level not in self.ocolors[offset]:
                return (-1, None)
            lst = self.ocolors[offset][level]
            if 1 < len(lst):
                # If this exception is raised, it means we have multiple colors at
                # the same level, which is unexpected for now. It will happen later
                # though.
                print('temporary failure, unexpected for now.')
            return (level, lst[0])

        level, cur = _sub(offset)
        left = _sub(offset - 1, level=level)[1]
        right = _sub(offset + 1, level=level)[1]

        pos = None
        if right is not None and cur == right:
            pos = HexViewColors.pos.BEGIN
        if left is not None and cur == left:
            if pos is None:
                pos = HexViewColors.pos.END
            else:
                pos = HexViewColors.pos.BOTH_ENDS
        if cur is not None and pos is None:
            pos = HexViewColors.pos.MIDDLE

        return (cur, pos)

    def gap_color(self, offset):
        cur, pos = self.color(offset)
        if pos in [HexViewColors.pos.BEGIN, HexViewColors.pos.MIDDLE]:
            return cur
        right, pos = self.color(offset + 1)
        if pos in [HexViewColors.pos.MIDDLE, HexViewColors.pos.END]:
            return right
        return None

    def colorize(self, offset_from, size, level, color):
        for offset in range(offset_from, offset_from + size):
            if offset not in self.ocolors:
                self.ocolors[offset] = dict()
            if level not in self.ocolors[offset]:
                self.ocolors[offset][level] = []
            self.ocolors[offset][level].append(color)

    def clear(self, offset_from, size, level, color):
        for offset in range(offset_from, offset_from + size):
            if offset not in self.ocolors:
                continue
            if level not in self.ocolors[offset]:
                continue
            try:
                idx = self.ocolors[offset][level].index(color)
                del self.ocolors[offset][level][idx]

                if not self.ocolors[offset][level]:
                    del self.ocolors[offset][level]

                if not self.ocolors[offset]:
                    del self.ocolors[offset]
            except ValueError:
                pass
