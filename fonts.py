import resources


MAIN_MENU = None
MAIN = None
SMALL = None
SMALLER = None
MONOSPACE = None


def load_fonts(lang):
    global MAIN_MENU, MAIN, SMALL, SMALLER, MONOSPACE
    if lang != 'ja_JP':
        MAIN_MENU = resources.load_font('Medieval Sharp/MedievalSharp.ttf', 48)
        MAIN = resources.load_font('Medieval Sharp/MedievalSharp.ttf', 36)
        SMALL = resources.load_font('Medieval Sharp/MedievalSharp.ttf', 24)
        SMALLER = resources.load_font('Medieval Sharp/MedievalSharp.ttf', 18)
        MONOSPACE = resources.load_font("LiberationMono/LiberationMono-Regular.ttf", 18)
    else:
        MAIN_MENU = resources.load_font('BabelStoneHan.ttf', 48)
        MAIN = resources.load_font('BabelStoneHan.ttf', 36)
        SMALL = resources.load_font('BabelStoneHan.ttf', 24)
        SMALLER = resources.load_font('BabelStoneHan.ttf', 18)
        MONOSPACE = resources.load_font("LiberationMono/LiberationMono-Regular.ttf", 18)

