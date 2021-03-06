# srddl/main.py - Main file, entry point of the program.
# Author: Franck Michea <franck.michea@gmail.com>
# License: New BSD License (See LICENSE)

import argparse
import pdb
import sys
import traceback

import srddl.core.frontend_loader


def main():
    parser = argparse.ArgumentParser(description='Templated hexadecimal editor.')

    dgroup = parser.add_argument_group(title='srddl debugging features')
    dgroup.add_argument('-b', '--backtrace', action='store_true', default=False,
                        help='print backtrace on error (default with --pdb).')
    dgroup.add_argument('-P', '--pdb', action='store_true', default=False,
                        help='start pdb debugger on exception.')

    frontends = srddl.core.frontend_loader.load_frontends(parser.add_subparsers())

    args, func = parser.parse_args(sys.argv[1:]), None
    if hasattr(args, 'func'):
        func = args.func
    elif not sys.stdin.isatty() and 'gui' in frontends:
        func = frontends['gui'].parser.get_default('func')
    if func is not None:
        try:
            func(args)
        except Exception as err:
            if args.backtrace or args.pdb:
                traceback.print_exc()
            if args.pdb:
                pdb.post_mortem(sys.exc_info()[2])
            elif not args.backtrace:
                header, output = 'ERROR: ', []
                for txt in str(err).splitlines():
                    output.append(' ' * len(header) + txt)
                output = header + '\n'.join(output)[len(header):]
                sys.exit(output)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
