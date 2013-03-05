# srddl/fields/padding.py - Padding fields used to fill blanks.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import srddl.core.helpers as sch

from srddl.core.abstract import AbstractField

PaddingMode = sch.enum(TAKE=0, FILL=1)

class Padding(AbstractField): pass
