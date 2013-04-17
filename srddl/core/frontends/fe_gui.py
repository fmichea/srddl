import collections
import sys

GUI_ON = True
try:
    from PySide import QtGui, QtCore
except ImportError:
    GUI_ON = False

import srddl.core.frontend_loader as scf

class GUI(scf.Frontend):
    class Meta:
        name = 'gui'
        help = 'graphical interface!'
        enabled = GUI_ON

    def process(self, args):
        app = QtGui.QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())

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
                'label': '&Preferences', 'name': 'preferences', 'enabled': False,
            },
        ],
    }),
])

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super().__init__()

        # Central widget.
        widget = QtGui.QWidget()
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
