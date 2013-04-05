import srddl.core.frontend_loader as scf

class Curses(scf.Frontend):
    class Meta:
        name = 'curses'
        help = 'awesome curses ui!'

    def process(self, args):
        print('args:', args)
