#!/usr/bin/env python

from utils import read
from distutils.core import setup


if __name__ == '__main__':
    setup(
        name = "Ice Emblem",
        version = read('VERSION').strip('\n'),
        author = "Elia Argentieri",
        author_email = "elia.argentieri@openmailbox.org",
        description = "Ice Emblem aims to be a completely free software clone of Fire Emblem.",
        license = "GPLv3",
        keywords = "game videogame pygame",
        url = "https://elinvention.ovh/progetti/ice-emblem/",
        packages = ['ice_emblem'],
        long_description = read('README.md'),
        classifiers = [
            "Development Status :: 1 - Planning",
            "Topic :: Videogame",
            "License :: OSI Approved :: GPLv3 License",
        ], requires=['pygame', 'PyYAML']
    )
