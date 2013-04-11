import curses
import curses.textpad
import sys
import time
import string

import srddl.core.frontend_loader as scf
import srddl.core.helpers as sch

import srddl.data as sd

LOGS = open('/tmp/curses_logs.txt', 'w')

def _write(*args):
    LOGS.write(' '.join(str(s) for s in args) + '\n')
    LOGS.flush()

class Curses(scf.Frontend):
    class Meta:
        name = 'curses'
        help = 'awesome curses ui!'
        enabled = sys.stdin.isatty()

    def process(self, args):
        try:
            cw = CursesMainWindow()
            cw.main()
        finally:
            curses.endwin()


class CursesWindow(sch.NamedRecord):
    class Meta:
        fields = ['x', 'y', 'width', 'height', 'displayed']

    def __init__(self, mw, parent, *args, **kwargs):
        if 'displayed' not in kwargs:
            kwargs['displayed'] = True
        nb_fields = len(self.metaconf('fields'))
        super().__init__(*(list(args) + [0] * nb_fields)[:nb_fields], **kwargs)

        self.mw, self.parent, self.window, self._create = mw, parent, None, True
        self.resize()

    @property
    def x(self):
        x = self._x
        if x < 0:
            x += self.parent.getmaxyx()[1]
        return x

    @property
    def y(self):
        y = self._y
        if y < 0:
            y += self.parent.getmaxyx()[0]
        return y

    @property
    def width(self):
        width = self._width
        if width <= 0:
            width += self.parent.getmaxyx()[1] - self.x
        return width

    @property
    def height(self):
        height = self._height
        if height <= 0:
            height += self.parent.getmaxyx()[0] - self.y
        return height

    @property
    def displayed(self):
        return self._displayed

    @displayed.setter
    def displayed(self, value):
        if value is True:
            self._displayed = self._create = True

    def redraw(self):
        if not self._displayed:
            return
        self.window.refresh()

    def resize(self):
        if not self._displayed:
            return
        if self._create:
            args = [self.height, self.width, self.y, self.x]
            self.window = self.parent.derwin(*args)
        else:
            self.window.mvwin(self.y, self.x)
            self.window.resize(self.height, self.width)


class CursesStatusBar(CursesWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.msgs = []
        self.addstr('Welcome!')

    def addstr(self, txt, timeout=0):
        if timeout == 0:
            self.msgs.append((txt, 0))
        else:
            self.msgs.append((txt, time.time() + timeout))

    def redraw(self):
        if not self._displayed:
            return
        while self.msgs[-1][1] != 0 and self.msgs[-1][1] < time.time():
            self.msgs.pop()
        self.window.addstr(0, 1, self.msgs[-1][0])
        self.window.clrtobot()
        super().redraw()

    def ask(self, prompt):
        self.addstr(prompt)

        win = self.window.derwin(0, len(prompt) + 1)
        tb = curses.textpad.Textbox(win, insert_mode=True)
        self.redraw()
        def validate_input(a):
            _write('a =', a)
            if a in [ord(c) for c in string.hexdigits]:
                return a
            if a in [1, 4, 5, 7, 263, 10, 11]:
                return a
            return None # discard input.
        res = tb.edit(validate_input)

        self.msgs.pop()
        self.redraw()
        return res

    def resize(self):
        if not self._displayed:
            return
        super().resize()
        self.window.bkgd(' ', curses.A_REVERSE)

_CHARS = string.ascii_letters + string.digits + string.punctuation

class CursesHexWindow(CursesWindow):
    def redraw(self):
        line, len_addr = 1, len(hex(len(self.mw.data)))
        for off, data in self.mw.data.view(self.height - 2).items():
            blocks, txts, cursor_byte, column = [], [], None, 0
            for it in zip(*([iter(data)] * (len(data) // 2))):
                def byte_display(x):
                    nonlocal column, cursor_byte
                    res, view = '{:02x}'.format(x), self.mw.data.view
                    if (view.line == off // sd.DataView.COLUMN_SIZE and
                        view.column == column):
                        res, cursor_byte = 'XX', res
                    column += 1
                    return res
                blocks.append(' '.join(byte_display(x) for x in it))
                txts.append(''.join(chr(x) if chr(x) in _CHARS else '.'
                            for x in it if it))
            res = '{offset:#0{laddr}x}:  {blocks}  |{txts}|'.format(
                offset=off, laddr=len_addr,
                blocks='  '.join(blocks),
                txts=' '.join(txts),
            )
            self.window.addstr(line, 1, res)
            if cursor_byte is not None:
                self.window.addstr(line, res.index('XX') + 1, cursor_byte,
                                   curses.A_REVERSE)
            line += 1
        super().redraw()


class KeyBinding(sch.NamedRecord):
    class Meta:
        fields = ['key', 'func', 'help', 'verbose']

PAGESIZE = 20

class CursesMainWindow:
    def __init__(self):
        self.screen, self.running = curses.initscr(), True
        self._line, self.data = 0, sd.FileData('/bin/ls')

        # curses configuration.
        curses.noecho()
        curses.curs_set(0)
        curses.halfdelay(8)
        self.screen.keypad(1)

        # initialize all windows.
        self.windows, windows_init = dict(), {
            'hexdump': (CursesHexWindow, [0, 0, 80, -1], {}),
            'status_bar': (CursesStatusBar, [0, -1, 0, 1], {}),
        }
        def init_subwindows(parent, init, windows):
            for name, (klass, vals, wlst) in init.items():
                windows[name] = (klass(self, parent, *vals), dict())
                windows[name][0].redraw()
                init_subwindows(windows[name][0], wlst, windows[name][1])
        init_subwindows(self.screen, windows_init, self.windows)

    def window(self, name):
        res, names = self.windows, name.split('.')
        names, name = names[:-1], names[-1]
        for it in names:
            res = res[it][1]
        return res[name][0]

    def iter_windows(self, func, windows=None):
        if windows is None:
            windows = self.windows
        for win, subwins in windows.values():
            func(win)
            self.iter_windows(func, windows=subwins)
        self.screen.refresh()

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, value):
        self._line = max(min(value, len(self.data) - PAGESIZE * 16), 0)

    def main(self):
        def quit_program():
            self.running = False
        def up():
            self.data.view.up()
            self.redraw_windows(['hexdump'])
        def right():
            self.data.view.right()
            self.redraw_windows(['hexdump'])
        def down():
            self.data.view.down()
            self.redraw_windows(['hexdump'])
        def left():
            self.data.view.left()
            self.redraw_windows(['hexdump'])
        def ppage():
            self.data.view.pageup()
            self.redraw_windows(['hexdump'])
        def npage():
            self.data.view.pagedown()
            self.redraw_windows(['hexdump'])
        def resize_term():
            self.iter_windows(lambda win: win.resize())
            self.iter_windows(lambda win: win.redraw())
        def goto_line():
            i = self.window('status_bar').ask('Offset: 0x')
            if len(i) == 0:
                return
            self.data.view.offset = int(i, 16)
            self.redraw_windows(['hexdump'])
        keybindings = [
            ('NOT IN HELP', 0, [
                KeyBinding([curses.KEY_RESIZE], resize_term),
            ]),
            ('General key bidings:', 1, [
                #KeyBinding('h', display_help, 'displays this help'),
                KeyBinding(['q'], quit_program, 'close the current window'),
            ]),
            ('Movements:', 1, [
                KeyBinding(['g'], goto_line, ''),
                KeyBinding(['k', curses.KEY_UP], up, '', verbose='k, up'),
                KeyBinding(['j', curses.KEY_DOWN], down, '', verbose='j, down'),
                KeyBinding(['l', curses.KEY_RIGHT], right, '', verbose='l, right'),
                KeyBinding(['h', curses.KEY_LEFT], left, '', verbose='h, left'),

                KeyBinding([curses.KEY_PPAGE], ppage, 'scrolls up few lines of hexdump', verbose='pageup'),
                KeyBinding([curses.KEY_NPAGE], npage, 'scrolls down few lines of hexdump', verbose='pagedown'),
            ]),
        ]
        while self.running:
            # Redraw all the windows always refreshed.
            self.redraw_windows()

            c = self.screen.getch()
            if c != -1:
                if 0 < c < 255:
                    c = chr(c)
                found = False
                for _, _, bindings in keybindings:
                    for binding in bindings:
                        if c in binding.key:
                            binding.func()
                            found = True
                            break
                    if found:
                        break
                if not found:
                    txt = 'Unknwon key binding, try \'h\' to see them all.'
                    self.window('status_bar').addstr(txt, 2)

    def redraw_windows(self, windows=None):
        if windows is None:
            windows = []
        windows.extend(['status_bar'])
        for window in windows:
            self.window(window).redraw()
        self.screen.refresh()
