# Changelog

## Version 0.3 (31-07-2019)

Added:

- Sphinx documentation in doc folder.
- python type annotations.
- Room class abstraction. It is a composable tree data structure with many functionalities.
- Add Tween class to implement animations.
- Add NinePath class to implement nine-patch textures.
- Android like two-pass (measure and layout) system to implement responsive and configurable (via Gravity and LayoutParams) container views.
- Add a spinner next to the FPS counter to make more clear what's happening.
- Animation of AI turn.

Changed:

- Huge refactoring. The majority of the code now uses the Room abstraction.
- Spread code across many modules.
- Many bugs fixed and others added :)
- Improved overall performance thanks to profiling.
- Only the part of surface that changed is filled.

Unfortunately I don't think this changelog is actually complete, because I didn't fill it as I progressed. I will try to be more careful next time :)

## Version 0.2 (03-11-2016)

- English and Italian languages thanks to gettext translations support
- Very simple AI to fight against for now (next year I'm going to study AI at university ;-)
- Settings menu with full-screen and resizeable window support
- reduced CPU usage
- more sound effects (attack, critical, null, miss, exp etc...)
- it is now possible to properly scroll the view

## Version 0.1 (22-05-2015)

- First release
- Very simple gameplay
- Single player mode without AI
- support tmx files
