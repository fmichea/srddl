import collections
import functools
import itertools
import math
import sys

GUI_ON = True
try:
    from PySide import QtGui, QtCore
except ImportError:
    GUI_ON = False

import srddl.core.fields as scf
import srddl.core.frontend_loader as scfe
import srddl.core.frontends.fe_common as scfc
import srddl.core.ftdetect as scft
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

        # Colors used to recognize the fields.
        'c1#fg': QtGui.QColor(15, 9, 44),
        'c1#bg': QtGui.QColor(149, 251, 255),
        'c2#fg': QtGui.QColor(7, 18, 47),
        'c2#bg': QtGui.QColor(255, 175, 221),
        'c3#fg': QtGui.QColor(79, 5, 0),
        'c3#bg': QtGui.QColor(165, 213, 62),
        'c4#fg': QtGui.QColor(0, 0, 0),
        'c4#bg': QtGui.QColor(249, 255, 37),
        'c5#fg': QtGui.QColor(82, 57, 21),
        'c5#bg': QtGui.QColor(141, 255, 206),
        'c6#fg': QtGui.QColor(165, 212, 62),
        'c6#bg': QtGui.QColor(61, 9, 5),
        'c7#fg': QtGui.QColor(38, 8, 29),
        'c7#bg': QtGui.QColor(255, 175, 0),
    }

    FONTS = {
        'monospace': QtGui.QFont("DejaVu Sans Mono"),
    }

    class HexView(QtGui.QAbstractScrollArea):
        def __init__(self, parent=None):
            super().__init__(parent=parent)

            # Colors.
            self.colors, self._fu = scfc.HexViewColors(), False

            # Viewport configuration.
            self.viewport().setAttribute(QtCore.Qt.WidgetAttribute.WA_StaticContents)
            self.viewport().setBackgroundRole(QtGui.QPalette.Base)
            self.viewport().setFocusProxy(self)
            self.viewport().setFocusPolicy(QtCore.Qt.WheelFocus)

            # Data view.
            self.set_data(None)

            # Font configuration.
            self.setFont(FONTS['monospace'])

        def set_data(self, data):
            if data is None:
                self._dv = None
                self.setFixedWidth(16777215) # Find QWIDGETSIZE_MAX.
                self.colors.empty()
            else:
                self._dv, self._fu = sd.DataView(data), True
            self._update_scrollbar()
            self.viewport().repaint()

        @property
        def x(self):
            return self.horizontalScrollBar().value()

        @property
        def y(self):
            return self.verticalScrollBar().value()

        def paintEvent(self, event):
            super().paintEvent(event)

            if self._dv is None:
                return

            line = self.y // self._line_height()
            for it, (addr, data) in enumerate(self._dv(line, self._lines() + 1).items()):
                y = self.print(it, 0, '{}:'.format(addr), color='addr')

                cur_offset = int(addr, 16)
                for d in data['data']:
                    y += 15
                    for b in d:
                        color = self.colors.color(cur_offset)[0]
                        y += self.print(it, y, b, color=color)
                        cur_offset += 1

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
            if self._fu:
                self.setFixedWidth(y + 10)
                self._fu = True

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
            if self._dv is None:
                return self.verticalScrollBar().setMaximum(0)
            height = self._line_height()
            maximum = self._dv.max_lines() * height - self.viewport().rect().height()

            self.verticalScrollBar().setSingleStep(height)
            self.verticalScrollBar().setPageStep(height * sd.DataView.PAGE_SIZE)
            self.verticalScrollBar().setMaximum(maximum)

        def _lines(self, func=math.ceil):
            return func(self.viewport().rect().height() / self._line_height())

        def _line_height(self):
            return self.fontMetrics().height() + 4

    class StructureTreeWidget(QtGui.QTreeWidget):
        class LegendRectWidget(QtGui.QIcon):
            def __init__(self, color):
                width, height = 35, 20
                try:
                    img = QtGui.QImage(width, height, QtGui.QImage.Format_ARGB32)
                    painter = QtGui.QPainter(img)
                    painter.fillRect(0, 0, width, height, COLORS[color + '#fg'])
                    painter.fillRect(1, 1, width - 2, height - 2, COLORS[color + '#bg'])
                finally:
                    painter.end()
                super().__init__(QtGui.QPixmap(img))

        class CustomTreeItem(QtGui.QTreeWidgetItem):
            def __init__(self, elem, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.setFont(0, FONTS['monospace'])
                self.elem = elem

        class StructTreeItem(CustomTreeItem):
            def __init__(self, struct, parent=None):
                res = '{offset}: {name} structure of size {size}.'.format(
                    offset = hex(struct['offset']),
                    name = struct.__class__.__name__,
                    size = struct['size'],
                )
                super().__init__(struct, [res], parent=parent)

        class BoundValueTreeItem(CustomTreeItem):
            def __init__(self, bv, color, parent=None):
                self.color = color

                # Description.
                res = []
                if bv['field']['path'] is not None:
                    res.append('{}:'.format(bv['field']['path']))
                if bv['field']['description'] is not None:
                    res.append('{}'.format(bv['field']['description']))
                else:
                    res.append('[no description]')
                if (bv['display_value'] is not None and
                    '\n' not in bv['display_value']):
                    res.append('with value {}'.format(bv['display_value']))
                if bv['description'] is not None:
                    res[-1] += ':'
                    res.append('{}'.format(bv['description']))
                res = ' '.join(res)
                if not res.endswith('.'):
                    res += '.'

                super().__init__(bv, [res], parent=parent)
                self.setIcon(0, StructureTreeWidget.LegendRectWidget(color))

        class ValueTreeItem(CustomTreeItem):
            def __init__(self, value, parent=None):
                res = '{name}: {value}'.format(
                    name=value['name'],
                    value=value['display_value']
                )
                super().__init__(value, [res], parent=parent)

        def __init__(self, hexview, parent=None):
            super().__init__(parent=parent)
            self.hexview = hexview

            self.itemExpanded.connect(self._itemExpand_handler)
            self.itemCollapsed.connect(functools.partial(
                self._itemExpand_handler, expand=False
            ))
            self.set_data(None, None)

        def set_data(self, ft, data):
            if ft is None:
                self.clear()
                self.setVisible(False)
                return

            ft.setup(data)
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
                    funcname = _visit_func_getter(tpl[0])
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
                    item = StructureTreeWidget.StructTreeItem(struct)
                    colors = itertools.cycle(['c{}'.format(i) for i in range(1, 8)])
                    for field_name in struct['fields']:
                        field = getattr(struct, field_name)
                        _visit_tree(item, (field, next(colors)), indent=indent+1)
                    root.addChild(item)
                def _visit_boundvalue(tmp):
                    bv, color = tmp
                    item = StructureTreeWidget.BoundValueTreeItem(bv, color)
                    _visit_tree(item, bv['value'])
                    root.addChild(item)
                def _visit_value(value):
                    root.addChild(StructureTreeWidget.ValueTreeItem(value))
                lcls, funcname = locals(), _visit_func_getter(elem)
                if funcname is not None:
                    lcls[funcname](elem)
            _visit_tree(self.invisibleRootItem(), data.mapped)
            self.setHeaderLabel('{name} - {abstract}'.format(
                name=ft['name'], abstract=ft['abstract']
            ))
            self.setVisible(True)

        def _itemExpand_handler(self, item, expand=True):
            if isinstance(item, StructureTreeWidget.BoundValueTreeItem):
                if item.childCount() == 1:
                    item.child(0).setExpanded(expand)
            if isinstance(item, StructureTreeWidget.StructTreeItem):
                if expand:
                    func = self.hexview.colors.colorize
                else:
                    func = self.hexview.colors.clear
                def _apply_func_to_tree(item):
                    level, parent = 0, item.parent()
                    while parent:
                        parent, level = parent.parent(), level + 1
                    for it_nb in range(item.childCount()):
                        it = item.child(it_nb)
                        if isinstance(it, StructureTreeWidget.BoundValueTreeItem):
                            off, sz = it.elem['offset'].byte, it.elem['size'].byte
                            func(off, sz, level, it.color)
                        if it.isExpanded():
                            _apply_func_to_tree(it)
                _apply_func_to_tree(item)
                self.hexview.viewport().repaint()


    class FileOpenerOptions(QtGui.QDialog):
        def __init__(self, filetypes, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.setWindowTitle('File options')

            # First transform file types.
            title = lambda ft, reason: '{} - {}'.format(ft['name'], reason)
            self._filetypes = dict((title(a, b), a) for a, b in filetypes)

            # Main layout: vertical box.
            self._main_layout = QtGui.QVBoxLayout()

            # Creating the form.
            self._form_groupBox = QtGui.QGroupBox('File Information')
            self._form_layout = QtGui.QFormLayout(parent=self)
            ## File detection selection for decoder.
            self._ft_decoder = QtGui.QComboBox()
            self._ft_decoder.setEditable(False)
            tmp = list(sorted(self._filetypes))
            tmp.append('Don\'t use any file decoder.')
            self._ft_decoder.addItems(tmp)
            self._form_layout.addRow('File type decoder:', self._ft_decoder)
            ## Other options.
            self._ro_option = QtGui.QCheckBox()
            self._form_layout.addRow('Open read-only:', self._ro_option)
            self._form_groupBox.setLayout(self._form_layout)
            self._main_layout.addWidget(self._form_groupBox)

            # Buttons to accept/cancel menu.
            tmp = QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
            self._button_box = QtGui.QDialogButtonBox(tmp)
            self._button_box.accepted.connect(self.accept)
            self._button_box.rejected.connect(self.reject)
            self._main_layout.addWidget(self._button_box)

            self.setLayout(self._main_layout)

        def chosen_ft(self):
            text = self._ft_decoder.itemText(self._ft_decoder.currentIndex())
            return self._filetypes.get(text)

        def chosen_ro(self):
            return self._ro_option.checkState() == QtCore.Qt.Checked


    class MainWindow(QtGui.QMainWindow):
        def __init__(self):
            super().__init__()

            # General attributes.
            self.data, self.fts = None, scft.FileTypesLoader()

            # Window title.
            self.setWindowTitle('Welcome! - SRDDL')

            # Central widget.
            layout = QtGui.QHBoxLayout()

            self.hexview = HexView()
            self.structtree = StructureTreeWidget(self.hexview)

            layout.addWidget(self.hexview)
            layout.addWidget(self.structtree)

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

        def _open_act_triggered(self):
            kwds = dict(caption='Open Binary File')
            filename = QtGui.QFileDialog.getOpenFileName(self, **kwds)[0]
            if filename == '':
                return
            self.data = sd.FileData(filename)

            options = FileOpenerOptions(self.fts.filter(self.data))
            options.exec_()

            if not options.chosen_ro():
                self.data = sd.FileData(filename, mode=sd.FileData.Mode.RDWR)
            ft = options.chosen_ft()

            self._file_menus_toggle(False)
            self.hexview.set_data(self.data)
            self.structtree.set_data(ft, self.data)

        def _save_act_triggered(self):
            self.data.flush()

        def _close_act_triggered(self):
            self.data = None
            self._file_menus_toggle(True)
            self.hexview.set_data(None)
            self.structtree.set_data(None, None)

        def _file_menus_toggle(self, enabled):
            self._open_act.setEnabled(enabled)
            self._save_act.setEnabled(not enabled and not self.data.ro)
            self._saveAs_act.setEnabled(not enabled and not self.data.ro)
            self._close_act.setEnabled(not enabled)
