#!/usr/bin/env python

import os
from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "Ice Emblem",
    version = "0.1",
    author = "Elia Argentieri",
    author_email = "elia.argentieri@openmailbox.org",
    description = "Ice Emblem aims to be a completely free software clone of Fire Emblem.",
    license = "GPLv3",
    keywords = "game videogame pygame",
    url = "https://elinvention.it/pagine/ice-emblem.html",
    packages=['ice_emblem'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Topic :: Videogame",
        "License :: OSI Approved :: GPLv3 License",
    ],
)
