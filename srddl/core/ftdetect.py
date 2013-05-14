import os

import srddl.core.helpers as sch
import srddl.models as sm

class FileTypesLoader:
    def __init__(self):
        self.fts = dict()
        main_root = os.path.join(os.path.dirname(__file__), '..', 'filetypes')
        def sub(cls):
            try:
                tmp = cls()
                if tmp['name'] in self.fts:
                    raise sch.FileTypeNameError()
                self.fts[tmp['name']] = tmp
            except TypeError:
                pass
        sch.class_loader(main_root, sm.FileType, sub)

    def filter(self, data):
        possibilities = set()
        for ft in self.fts.values():
            for ext in ft['extensions']:
                if data.filename.endswith('.{}'.format(ext)):
                    possibilities.add((ft, 'Extension {} recognized.'.format(ext)))
            else:
                if ft.check(data):
                    possibilities.add((ft, 'File type recognized data.'))
        return list(possibilities)
