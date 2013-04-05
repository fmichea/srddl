# srddl/core/exceptions.py - Exceptions used only in core modules.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

# ----- Front-end loader exceptions --------------------------------------------

class FrontEndConfigurationError(Exception):
    def __init__(self, klass, name):
        self.klass, self.name = klass, name

    def __str__(self):
        res = 'Configuration for "{name}" key was not found for front-end {fe}.'
        return res.format(name = self.name, fe = self.klass.__name__)
