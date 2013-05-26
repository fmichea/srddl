# fe_common.py - Common logic shared with all frontends.

import collections
import copy

import srddl.core.helpers as sch

class Color:
    def __init__(self, name, **kwargs):
        self.name, self.positions = name, kwargs.copy()
        self.tmp_props, self.fixed_props = set(), set()

    def __hash__(self):
        return hash(self.name)

    def toggle_property(self, temporary, prop):
        props = self.tmp_props if temporary else self.fixed_props
        if prop in props: props.discard(prop)
        else: props.add(prop)

    @property
    def properties(self):
        return set(self.tmp_props | self.fixed_props)


class ColorManager:
    # This properties are not filters, but only
    SPECIAL_PROPERTIES = ['enabled']

    def __init__(self, colors, tf=None, properties=None):
        self._tf, self._colors = tf or (lambda x: x), dict()
        self._properties = collections.OrderedDict(properties or [])
        for c in colors:
            self._colors[c.name] = c

    def color(self, name):
        if name is None:
            return None
        elif '@' in name:
            name, properties = name.split('@', 1)
            properties = properties.split(',')
        else:
            properties = []
        c = copy.deepcopy(self._colors.get(name))
        for prop in properties:
            c.toggle_property(False, prop)
        return c

    def color2obj(self, color, pos, raises=True):
        if color is None:
            return None
        if isinstance(color, str):
            color = self.color(color)
        c = color.positions.get(pos)
        if c is None:
            if raises:
                m = 'Position "{}" is unknown in color "{}".'.format(pos, c.name)
                raise ValueError(m)
            return None
        c = self._tf(c)
        if c is None:
            if raises:
                m = 'Transformation of the object returned None.'
                raise ValueError(m)
            return None
        properties = color.properties
        for p, func in self._properties.items():
            if p not in color.properties:
                continue
            c = func(c)
            properties.discard(p)
        properties = [p for p in properties
                      if p not in ColorManager.SPECIAL_PROPERTIES]
        if properties:
            if raises:
                p = ', '.join(list(properties))
                m = 'Properties "{}" is unknown of color manager.'.format(p)
                raise ValueError(m)
            return None
        return c


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
                level = -1
                for lvl, lst in self.ocolors[offset].items():
                    if [x for x in lst if 'enabled' in x.properties]:
                        level = max(level, lvl)
                if level == -1:
                    return (-1, None)
            elif level not in self.ocolors[offset]:
                return (-1, None)
            lst = [x for x in self.ocolors[offset][level]
                   if 'enabled' in x.properties]
            if not lst:
                return (-1, None)
            elif 1 < len(lst):
                # If this exception is raised, it means we have multiple colors
                # at the same level, which is unexpected for now. It will happen
                # later though.
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
                pos = HexViewColors.pos.MIDDLE
        if cur is not None and pos is None:
            pos = HexViewColors.pos.BOTH_ENDS

        return (cur, pos)

    def empty(self):
        self.ocolors.clear()

    def gap_color(self, offset):
        cur, pos = self.color(offset)
        if pos in [HexViewColors.pos.BEGIN, HexViewColors.pos.MIDDLE]:
            return cur
        right, pos = self.color(offset + 1)
        if pos in [HexViewColors.pos.MIDDLE, HexViewColors.pos.END]:
            return right
        return None

    def add_color(self, offset_from, size, level, color):
        for offset in range(offset_from, offset_from + size):
            if offset not in self.ocolors:
                self.ocolors[offset] = dict()
            if level not in self.ocolors[offset]:
                self.ocolors[offset][level] = []
            self.ocolors[offset][level].append(color)

#    def toggle_color(self, offset_from, size, level, color, temporary=True):
#        enable = 'enabled' not in color.properties(temporary)
#        def sub(lst):
#            for c in lst:
#                if enable and 'enabled' in c.properties:
#                    msg = 'Can\'t enable two colors on the same level at the'
#                    msg += ' same time yet.'
#                    raise Exception(msg)
#            props = color.properties(temporary)
#            if enable: props.add('enabled')
#            else: props.discard('enabled')

    def set_property(self, offset_from, size, level, prop, enable, temporary=True):
        def sub(lst):
            for c in lst:
                props = c.tmp_props if temporary else c.fixed_props
                if enable:
                    props.add(prop)
                else:
                    props.discard(prop)
        self._apply_all(offset_from, size, level, sub)

    def toggle_property(self, offset_from, size, level, prop, temporary=True):
        def sub(lst):
            for c in lst:
                props = c.tmp_props if temporary else c.fixed_props
                if prop in props:
                    props.discard(prop)
                else:
                    props.add(prop)
        self._apply_all(offset_from, size, level, sub)

    def _apply_all(self, offset_from, size, level, func):
        if offset_from == -1 or size == -1:
            for levels in self.ocolors.values():
                for lvl, lst in levels.items():
                    if level != -1 and lvl < level:
                        continue
                    func(lst)
            return
        for offset in range(offset_from, offset_from + size):
            if offset not in self.ocolors:
                continue
            for lvl, lst in self.ocolors[offset].items():
                if lvl < level:
                    continue
                func(lst)
