# srddl/core/frontend_loader.py - Front-end loader to ease their creation.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import abc
import imp
import inspect
import os
import sys

import srddl.core.helpers as sch


class Frontend(sch.MetaConf, metaclass=abc.ABCMeta):
    class MetaBase:
        enabled = True
        default_args = True
        description = None

    def __init__(self):
        self.parser = None

    def frontend_init(self, subparser):
        if not self.metaconf('enabled'):
            return
        kwds = dict((it, self.metaconf(it)) for it in ['help', 'description'])

        # Argument subparser.
        self.parser = subparser.add_parser(self.metaconf('name'), **kwds)
        self.parser.set_defaults(func=self.process)

        # Default arguments available in all frontends, unless default_args is
        # set to False.
        if self.metaconf('default_args'):
            self.parser.add_argument('-T', '--type', action='store', metavar='T',
                                     help='type of file to use.')

        # Initialization,
        self.init()

    def init(self):
        '''Use this method to add arguments to the parser.'''

    @abc.abstractmethod
    def process(self, args):
        '''This method is called when the front-end is selected.'''

def load_frontends(argument_parser):
    main_root = os.path.join(os.path.dirname(__file__), 'frontends')
    frontends = []

    def sub(cls):
        try:
            tmp = cls()
            tmp.frontend_init(argument_parser)
            frontends[tmp.metaconf('name')] = tmp
        except TypeError:
            pass
    sch.class_loader(main_root, Frontend, sub)

    return frontends
