README of srddl
==============

/!\ Warning: This project is in heavy development and API can break anytime,
             sorry. You're more than welcome to follow it and patch bugs if you
             want though.

- Current state: Unpacking structures, see examples in `examples/` directory.
- Goal: Templated hexadecimal editor, to enhance working with binary files.

All current ideas are put in the TODO file. Check the sources!

Examples
--------

Here is a simple example, that might give you a better idea of what is a basic
usage of srddl:

    import srddl.data as sd
    import srddl.fields as sf
    import srddl.models as sm

    class A(sm.Struct):
        length = sf.IntField()
        data = sf.ArrayField(length, sf.IntField())

    # This data is read-only (automatic detection).
    data = '0a00010203040506070809'
    data = sd.Data(bytes.fromhex(data))

    # We will map structure A from offset 0 of data.
    a = A(data, 0)

    # Now we can play!
    print('Complete struture:', a)
    print('Length', a.length, a.length == 10, a.length['value'], sep=' | ')
    print('Data:', a.data, a.data[0] == 0, a.data[9] == 9, sep=' | ')

    # If data is not read-only, we can modify values, but if we change length,
    # data size is not affected yet (in TODO).
    # example: a.length = 5 # changes the first byte to 5 instead of 10.

You can find some more examples in `examples/` directory and a more complete
file decoder in `srddl/filetypes/` directory.

Features
--------

 - Structure unpacking, providing a lot of built-in fields, with advanced
   features like documentation, validity checking, ...
 - GUI Front-end aimed to render editing of structured file formats easy.

Installation
------------

Since this is only a pre-alpha-in-development-tool, there is no real way to
install it, though a setup.py is provided for easy install. I foster you to
install it in development mode (`python setup.py develop`), to be able to fetch
easily bug fixes with a simple `git pull` of the repository in your home :)
