import room
import gui
import resources
import display
import colors as c
import fonts as f
import state as s


class MapMenu(room.Room):
    def __init__(self, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.files = [(f, None) for f in resources.list_maps()]
        self.choose_label = f.MAIN_FONT.render(_("Choose a map!"), True, c.ICE, c.MENU_BG)
        self.menu = gui.Menu(self.files, f.MAIN_FONT, padding=(25, 25))
        self.menu.rect.center = display.window.get_rect().center
        self.add_child(self.menu)

    def draw(self):
        window = display.window
        window.fill(c.BLACK)
        self.rect.center = window.get_rect().center
        window.blit(self.image, self.rect)
        window.blit(self.choose_label, self.choose_label.get_rect(top=50, centerx=window.get_rect().centerx))
        self.menu.rect.center = window.get_rect().center
        super().draw()

    def loop(self, _events):
        return self.menu.choice is not None

    def end(self):
        super().end()
        map_path = resources.map_path(self.files[self.menu.choice][0])
        s.load_map(map_path)
