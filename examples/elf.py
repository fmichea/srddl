import time
import sys

import srddl.data as sd

from srddl.filetypes.elf import ELF

COUNT = 1
if 1 < len(sys.argv) and sys.argv[1] == 'benchmark':
    COUNT = 10
begin, d, e = time.perf_counter(), None, None
for _ in range(COUNT):
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = '/bin/ls'
    d = sd.FileData(filename, mode=sd.FileData.Mode.RDWR)

    e = ELF()
    e.setup(d)
elapsed = (time.perf_counter() - begin) / COUNT
print('Mean time on', COUNT, 'rounds: {:8.5f} seconds'.format(elapsed))
