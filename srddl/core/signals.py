# srddl/core/signal.py - Signal management stuff.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import srddl.exceptions as se

class _SignalHandler:
    def __init__(self, func, kwargs):
        self.func, self._kwargs = func, kwargs

    def __repr__(self):
        return 'SignalHandler {:#x} on {}'.format(id(self), self.func)

    def __call__(self, args):
        self.func(*args, **self._kwargs)


class Signal:
    def __init__(self, *args):
        self._signals = dict()
        for arg in args:
            self.create(arg)

    def create(self, signame):
        '''
        :param signame: Name to give to the signal, it will be its identifier.

        Creates a signal with the given signal name. This is mandatory because
        we will use strings for signal names and we don't want to subscribe
        to a signal that doesn't exist by mistake because of a typo.
        '''
        if signame in self._signals:
            raise se.SignalExistsError(signame)
        self._signals[signame] = dict()

    def subscribe(self, signame, func, **kwargs):
        '''
        :param signame: The name of the signal.
        :param func: The callback to call on signal trigger.
        :return: An id identifying the handler, used by unsubscribe.

        This function permits to subscribe to some signal. You must give a
        callback function that will be called on signal triggering.  You can
        add some keyword parameters that will also be given to the function, so
        that you can have "closures".
        '''
        if signame not in self._signals:
            raise se.SignalNotFoundError(signame, 'subscribing')
        for idx, handler in self._signals[signame].items():
            if handler.func is func:
                return idx
        sh = _SignalHandler(func, kwargs)
        self._signals[signame][id(sh)] = sh
        return id(sh)

    def unsubscribe(self, signame, idx):
        '''
        :param signame: The name identifying the signal.
        :param idx: The id returned by subscribe method.

        You can unsubscribe to a signal using this method. After this, the
        handler function won't be called again.
        '''
        if signame not in self._signals:
            raise se.SignalNotFoundError(signame, 'unsubscribing')
        if idx not in self._signals[signame]:
            raise se.SignalHandlerNotFoundError(signame, idx)
        del self._signals[signame][idx]

    def trigger(self, signame, *args):
        '''
        With this function you can trigger a signal.

        :param signame: The signal name to trigger.
        :param args: Arguments to give to the signal.
        '''
        if signame not in self._signals:
            raise se.SignalNotFoundError(signame, 'triggering')
        handlers = list(self._signals[signame].values())
        for handler in handlers:
            try:
                handler(args)
            except TypeError:
                raise se.SignalHandlerCallError(signame, handler)

    def signals(self):
        return list(self._signals.keys())
