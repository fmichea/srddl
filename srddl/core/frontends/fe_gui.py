import collections
import math
import sys

GUI_ON = True
try:
    from PySide import QtGui, QtCore
except ImportError:
    GUI_ON = False

import srddl.core.fields as scf
import srddl.core.frontend_loader as scfe
import srddl.data as sd
import srddl.models as sm

class GUI(scfe.Frontend):
    class Meta:
        name = 'gui'
        help = 'graphical interface!'
        enabled = GUI_ON

    def process(self, args):
        app = QtGui.QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())

if GUI_ON:
    MENUS = collections.OrderedDict([
        ('&File', {
            'label': 'file',
            'submenus': [{
                    'label': '&Open...', 'name': 'open',
                    'keybinding': QtGui.QKeySequence.Open,
                }, None, {
                    'label': '&Save', 'name': 'save', 'enabled': False,
                    'keybinding': QtGui.QKeySequence.Save,
                }, {
                    'label': 'Save &As...', 'name': 'saveAs', 'enabled': False,
                    'keybinding': QtGui.QKeySequence.SaveAs,
                }, None, {
                    'label': '&Close', 'name': 'close', 'enabled': False,
                    'keybinding': QtGui.QKeySequence.Close,
                }, {
                    'label': '&Exit', 'name': 'exit',
                    'keybinding': QtGui.QKeySequence.Quit
                },
            ],
        }),
        ('&Edit', {
            'label': 'edit',
            'submenus': [{
                    'label': '&Preferences', 'name': 'preferences',
                    'enabled': False,
                },
            ],
        }),
    ])

    COLORS = {
        'addr#bg': QtGui.QColor(240, 240, 240),
        'faded#fg': QtGui.QColor(200, 200, 200),
    }

    FONTS = {
        'monospace': QtGui.QFont("DejaVu Sans Mono"),
    }

    class HexView(QtGui.QAbstractScrollArea):
        def __init__(self, data, parent=None):
            super().__init__(parent=parent)

            # Viewport configuration.
            self.viewport().setAttribute(QtCore.Qt.WidgetAttribute.WA_StaticContents)
            self.viewport().setBackgroundRole(QtGui.QPalette.Base)
            self.viewport().setFocusProxy(self)
            self.viewport().setFocusPolicy(QtCore.Qt.WheelFocus)

            # Data view.
            self._dv = sd.DataView(data)

            # Font configuration.
            self.setFont(FONTS['monospace'])
            self.setFixedWidth(550)

        @property
        def x(self):
            return self.horizontalScrollBar().value()

        @property
        def y(self):
            return self.verticalScrollBar().value()

        def paintEvent(self, event):
            super().paintEvent(event)

            line = self.y // self._line_height()
            for it, (addr, data) in enumerate(self._dv(line, self._lines() + 1).items()):
                y = self.print(it, 0, '{}:'.format(addr), color='addr')

                for d in data['data']:
                    y += 15
                    for b in d:
                        y += self.print(it, y, b)

                y += 15
                y += self.print(it, y, '|', color='faded')
                for d in data['strings']:
                    for b in d:
                        kwds = dict(padding=0)
                        if b is None:
                            b = '.'
                            kwds['color'] = 'faded'
                        y += self.print(it, y, b, **kwds)
                    y += 10
                y += self.print(it, y - 10, '|', color='faded')

        def print(self, line, y, text, color=None, padding=2):
            painter = QtGui.QPainter(self.viewport())

            width = painter.fontMetrics().width(text) + padding * 2
            height = self._line_height()

            # Rectangle in which text will be drawn.
            rect = QtCore.QRectF(y, line * height, width, height)
            rect = rect.translated(0, -(self.y % self._line_height()))

            if color is not None and (color + '#fg') in COLORS:
                painter.setPen(COLORS[color + '#fg'])

            if color is not None and (color + '#bg') in COLORS:
                painter.fillRect(rect, COLORS[color + '#bg'])
            painter.drawText(rect, QtCore.Qt.AlignCenter, text)

            return width

        def resizeEvent(self, event):
            super().resizeEvent(event)
            self._update_scrollbar()

        def _update_scrollbar(self):
            height = self._line_height()
            maximum = self._dv.max_lines() * height - self.viewport().rect().height()

            self.verticalScrollBar().setSingleStep(height)
            self.verticalScrollBar().setPageStep(height * sd.DataView.PAGE_SIZE)
            self.verticalScrollBar().setMaximum(maximum)

        def _lines(self, func=math.ceil):
            return func(self.viewport().rect().height() / self._line_height())

        def _line_height(self):
            return self.fontMetrics().height() + 4


    class StructureTreeView(QtGui.QTreeView):
        def __init__(self, data, parent=None):
            super().__init__(parent=parent)

            self._data, rootModel = data, QtGui.QStandardItemModel()
            root = rootModel.invisibleRootItem()

            TREE = [
                (list, 'list'),
                (tuple, 'tuple'),
                (sm.Struct, 'struct'),
                (sd.Data.MappedData, 'mappeddata'),
                (scf.BoundValue, 'boundvalue'),
                (scf.Value, 'value'),
            ]
            def _visit_tree(root, elem, indent=0):
                def _visit_func_getter(elem):
                    for tmp in TREE:
                        t, funcname = tmp
                        if isinstance(elem, t):
                            return ('_visit_' + funcname)
                    return None
                def _visit_tuple(tpl):
                    funcname = _visit_func_getter(tpl[1])
                    if funcname is not None:
                        lcls[funcname](elem)
                def _visit_mappeddata(md):
                    _visit_list(md.values())
                def _visit_list(lst, key=None, gname=None, gval=None):
                    if key is not None:
                        lst = sorted(lst, key=key)
                    for l in lst:
                        if gval is not None:
                            l = (gname(l) if gname is not None else l, gval(l))
                        _visit_tree(root, l)
                def _visit_struct(struct):
                    print('  ' * indent, '+ Struct:', hex(struct['offset']), struct.__class__.__name__)
                    for field_name in struct['fields']:
                        field = getattr(struct, field_name)
                        _visit_tree(root, (field_name, field), indent=indent+1)
                def _visit_boundvalue(tmp):
                    name, boundvalue = tmp
                    print('  ' * indent, '+', name, ':', boundvalue['display_value'])
                    sv = None #boundvalue['subvalues']
                    if sv is not None:
                        _visit_tree(root, sv, indent=indent+1)
                def _visit_value(value):
                    print('  ' * indent, '+ Value:', value['display_value'])
                lcls, funcname = locals(), _visit_func_getter(elem)
                if funcname is not None:
                    lcls[funcname](elem)
            _visit_tree(root, data.mapped)
            #self.setModel(rootModel)

    class MainWindow(QtGui.QMainWindow):
        def __init__(self):
            super().__init__()

            # General attributes.
            self.data = sd.FileData('/usr/bin/cat')
            import examples.elf; self.data.map(0, examples.elf.ElfN_Ehdr)

            # Window title.
            self.setWindowTitle('Welcome! - SRDDL')

            # Central widget.
            layout = QtGui.QHBoxLayout();
            layout.addWidget(HexView(self.data))
            layout.addWidget(StructureTreeView(self.data))

            widget = QtGui.QWidget()
            widget.setLayout(layout)
            self.setCentralWidget(widget)

            # Menu.
            for menuName, menus in MENUS.items():
                menu = self.menuBar().addMenu(menuName)
                for submenu in menus['submenus']:
                    if submenu is None:
                        menu.addSeparator()
                        continue
                    # Configuration for each action.
                    conf = {'keybinding': None, 'enabled': True}
                    conf.update(submenu)

                    # Name of actions/triggered functions.
                    name = '_{}_act'.format(conf['name'])
                    name_fn = '{}_triggered'.format(name)

                    # Build action.
                    setattr(self, name, QtGui.QAction(conf['label'], menu))
                    act = getattr(self, name)

                    act.setEnabled(conf['enabled'])
                    if conf['keybinding'] is not None:
                        act.setShortcut(conf['keybinding'])
                    if 'status_tip' in conf:
                        act.setStatusTip(conf['status_tip'])
                    func = conf.get('func', getattr(self, name_fn, None))
                    if func is not None:
                        act.triggered.connect(func)
                    menu.addAction(act)
                setattr(self, '_{}_menu'.format(menus['label']), menu)

            # Status bar.
            self.statusBar().showMessage('Welcome!')

        def _exit_act_triggered(self):
            self.close()
