from setuptools import setup

setup(
    name = 'casio-fx-tools',
    description = 'Tools to save/load CASIO FX calculator programs and data',
    version = '1.0',
    author = 'Jan Wieck',
    author_email = 'jan@wi3ck.info',
    url = None,
    license = 'MIT',
    packages = ['casio_fx_tools'],
    entry_points = {
        'console_scripts': [
            'fx502p_load = casio_fx_tools.cmdline:fx502p_load',
            'fx502p_save = casio_fx_tools.cmdline:fx502p_save',
        ]
    }
)
