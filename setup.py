import sys
try:
    from setuptools import setup, find_packages
except ImportError:
    import distribute_setup
    distribute_setup.use_setuptools()
    from setuptools import setup, find_packages

if sys.version_info[0] != 3:
    msg = 'srddl is intended to be used with python 3 only (it uses specific '
    msg += 'features).\nMinimum version is not known yet, but this code was '
    msg += 'tested for python 3.3 at least (released September 29, 2012).'
    sys.exit(msg)

setup(
    # General information.
    name='srddl',
    description='Templated hexa-decimal editor.',
    url='https://bitbucket.org/kushou/srddl',

    # Version information.
    license='BSD',
    version='0.0.1a',

    # Author information.
    author='Franck Michea',
    author_email='franck.michea@gmail.com',

    # File information.
    install_requires=open('requirements.txt').readlines(),
    packages=find_packages(exclude=['tests', 'examples', 'doc']),
    entry_points = {'console_scripts': ['srddl = srddl.main:main']},

    # PyPI categories.
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
    ],
)
