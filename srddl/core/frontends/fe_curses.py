import sys
import time
import string

CURSES_ON = True
try:
    import urwid
except ImportError:
    CURSES_ON = False

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
        enabled = CURSES_ON and sys.stdin.isatty()

    def process(self, args):
        cw = CursesMainWindow()
        cw.main()


class KeyBinding(sch.NamedRecord):
    class Meta:
        fields = ['keys', 'function']


_KEYS = [('Ctrl', 'ctrl'), ('Alt', 'meta'), ('+', ' ')]

def _verbose_to_urwid_keys(keys):
    def sub(key):
        for verb, uverb in _KEYS:
            key = key.replace(verb, uverb)
        return key
    return [sub(key) for key in keys]

def _urwid_to_verbose(key):
    for verb, uverb in _KEYS:
        key = key.replace(uverb, verb)
    return key

if CURSES_ON:
    class StatusBar(urwid.AttrMap):
        def __init__(self, mw):
            self.wtext = urwid.Text('')
            super().__init__(self.wtext, 'footer')
            self.msgs, self.mw = [], mw
            self.add_text('Welcome!')

        def add_text(self, txt, timeout=0):
            if 0 < timeout:
                self.msgs.append((txt, time.time() + timeout))
                self.mw.loop.set_alarm_in(timeout, self._reload_text)
            else:
                self.msgs.append((txt, 0))
            self._set_text(txt)

        def _reload_text(self, obj, user_data):
            count, t0 = 0, time.time()
            for it in range(len(self.msgs)):
                idx = it - count
                if self.msgs[idx][1] and self.msgs[idx][1] < t0:
                    del self.msgs[idx]
                    count += 1
            if count:
                self._set_text(self.msgs[-1][0])

        def _set_text(self, markup):
            if isinstance(markup, str):
                markup = [markup]
            self.wtext.set_text([' '] + markup)


    class StatusBarAsker(urwid.Edit, metaclass=urwid.signals.MetaSignals):
        signals = ['ask_done']

        def __init__(self, *args, **kwargs):
            self.validator = kwargs.pop('validator', None)
            super().__init__(*args, **kwargs)

        def keypress(self, size, key):
            if key == 'enter':
                urwid.emit_signal(self, 'ask_done', self.get_edit_text())
            elif key == 'esc':
                urwid.emit_signal(self, 'ask_done', None)
            elif len(key) != 1 or self.validator is None or self.validator(key):
                super().keypress(size, key)


    class HexView(urwid.ListWalker):
        def __init__(self, data):
            self.focus = (0, 0)
            self.view = sd.DataView(data)

        def __getitem__(self, position):
            line, _ = position
            _write('position =', position)
            if 0 <= line and line < self.view.max_lines():
                addr, data = list(self.view(line, 1).items())[0]

                # Widgets for columns
                widgets = [('pack', urwid.Text([('addr', addr)]))]
                data = [[('pack', urwid.Text(b)) for b in d] for d in data['data']]
                widgets.extend([urwid.Columns(d, dividechars=1) for d in data])

                return urwid.Columns(widgets, dividechars=2, min_width=len(addr))
            raise IndexError

        def next_position(self, position):
            if position[0] < self.view.max_lines():
                return (position[0] + 1, position[1])
            raise IndexError

        def prev_position(self, position):
            if position[0] != 0:
                return (position[0] - 1, position[1])
            raise IndexError


class CursesMainWindow:
    def __init__(self):
        # Non-UI data.
        self.data = sd.FileData('/bin/ls')

        # Palette of colors.
        self.palette = [
            ('footer', 'black', 'light gray'),
            ('addr', 'white', 'black'),
        ]
        self.loop = None

        # Build main view.
        ## Body
        self.body = urwid.ListBox(HexView(self.data))

        ## Footer
        self.status_bar = StatusBar(self)

        ## Main view
        self.view = urwid.Frame(self.body, footer=self.status_bar)

        # Main loop
        self.loop = urwid.MainLoop(self.view, palette=self.palette,
                                   unhandled_input=self.unhandled_input)

    def unhandled_input(self, key):
        def exit_program(key):
            '''quit the program'''
            raise urwid.ExitMainLoop()
        def goto_offset(key):
            def validator(key):
                return key in string.hexdigits
            def done(offset):
                _write('offset select =', int(offset, 16))
            self.ask('Go to offset 0x', done, validator=validator)
        KEYBINDINGS = [
            ('General features:', 1, [
                KeyBinding(['q', 'Q'], exit_program),
            ]),
            ('Move arround:', 1, [
                KeyBinding(['g'], goto_offset),
            ]),
        ]
        for _, _, bindings in KEYBINDINGS:
            for binding in bindings:
                if key in _verbose_to_urwid_keys(binding.keys):
                    binding.function(key)
                    return True
        txt = 'Unknwon key binding \'{}\', try \'h\' to see them all.'
        self.status_bar.add_text(txt.format(_urwid_to_verbose(key)), timeout=2)

    def ask(self, prompt, callback, validator=None):
        edit = StatusBarAsker(' ' + prompt, validator=validator)
        def ask_done(content):
            urwid.disconnect_signal(self, edit, 'ask_done', ask_done)
            self.view.set_focus('body')
            self.view.set_footer(self.status_bar)
            if content is not None:
                callback(content)
        self.view.set_footer(urwid.AttrMap(edit, 'footer'))
        self.view.set_focus('footer')
        urwid.connect_signal(edit, 'ask_done', ask_done)

    def main(self):
        self.loop.run()

