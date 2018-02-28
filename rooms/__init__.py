import pathlib
import sys


path = pathlib.Path(__file__).resolve().parent

for py in [f.stem for f in path.glob("*.py") if f.stem != '__init__']:
    mod = __import__('.'.join([__name__, py]), fromlist=[py])
    classes = [getattr(mod, x) for x in dir(mod) if isinstance(getattr(mod, x), type)]
    for cls in classes:
        setattr(sys.modules[__name__], cls.__name__, cls)
