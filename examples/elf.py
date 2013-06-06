import time
import sys

import srddl.data as sd

from srddl.filetypes.elf import ELF

COUNT = 1
if 1 < len(sys.argv) and sys.argv[1] == 'benchmark':
    COUNT = 10
begin, d, e = time.perf_counter(), None, None
for _ in range(COUNT):
    d = sd.FileData('/bin/ls')
    e = ELF()
    e.setup(d)
elapsed = (time.perf_counter() - begin) / COUNT
print('Mean time on', COUNT, 'rounds: {:8.5f} seconds'.format(elapsed))
