import os

import srddl.core.helpers as sch
import srddl.models as sm

def load_filetypes():
    main_root = os.path.join(os.path.dirname(__file__), '..', 'filetypes')
    fts = dict()

    def sub(cls):
        try:
            tmp = cls()
            fts[tmp['name']] = tmp
        except TypeError:
            pass
    sch.class_loader(main_root, sm.FileType, sub)

    return fts

def filter_filetypes(fts, data):
    possibilities = set()

    for ft in fts.values():
        for ext in ft['extensions']:
            if data.filename.endswith('.{}'.format(ext)):
                possibilities.add((ft, 'Extension {} recognized.'.format(ext)))
        else:
            if ft.check(data):
                possibilities.add((ft, 'File type recognized data.'))
    return list(possibilities)
