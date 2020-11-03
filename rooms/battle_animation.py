import pygame
import pygame.locals as p

import gui
import fonts as f
import room
import rooms
import display
import state as s
import sounds
import colors as c

from unit import Unit, Team
from room import Layout, Gravity

from gettext import gettext as _


class AttackAnimation(gui.Tween):
    def __init__(self, image, vector, on_animation_finished):
        super().__init__(vector, 200, callback=on_animation_finished, die_when_done=False)
        self.text = gui.Label("", f.SMALL, visible=False)
        self.image = gui.Image(image, die_when_done=False)
        self.add_children(self.text, self.image)


class BattleUnitStats(gui.LinearLayout):
    def __init__(self, unit: Unit, vector, on_animation_finished, **kwargs):
        super().__init__(padding=100, **kwargs)
        self.unit = unit
        self.animation = AttackAnimation(unit.image, vector, on_animation_finished)
        self.name = gui.Label(unit.name, f.MAIN, txt_color=unit.team.color)
        self.life = gui.LifeBar(points=unit.health_max, value=unit.health)
        self.stats = gui.Label(str(unit), f.SMALL)
        self.add_children(self.animation, self.name, self.life, self.stats)

    def update(self):
        self.life.value = self.unit.health
        self.stats.set_text(str(self.unit))


def broken_screen(unit):
    sounds.play('broke')
    room.run_room(gui.Label("%s is broken" % unit.weapon.name, f.SMALL, txt_color=c.RED))


class BattleAnimation(gui.LinearLayout):
    def __init__(self, attacking: Unit, defending: Unit, **kwargs):
        super().__init__(wait=False, orientation=gui.Orientation.HORIZONTAL, **kwargs)
        self.attacking = attacking
        self.defending = defending
        center = Layout(gravity=Gravity.CENTER)
        self.att_stats = self.att_swap = BattleUnitStats(self.attacking, (50, 0), self.anim_finished, layout=center)
        self.def_stats = self.def_swap = BattleUnitStats(self.defending, (-50, 0), self.anim_finished, layout=center)
        self.add_children(self.att_stats, self.def_stats)
        self.at = self.dt = self.round = 0
        self.outcome = self.damage = None

    def begin(self):
        super().begin()

        if self.attacking.health <= 0:
            raise ValueError(f"{self.attacking} is dead!")
        if self.defending.health <= 0:
            raise ValueError(f"{self.defending} is dead!")
        if self.attacking.played:
            raise ValueError(f"{self.attacking} has already played!")

        self.attacking.prepare_battle()
        self.defending.prepare_battle()

        self.at, self.dt = self.attacking.number_of_attacks(self.defending)
        self.round = 1

        print(f"\r\n{'#' * 12} {self.attacking.name} vs {self.defending.name} {'#' * 12}")
        att_str = _("%s is going to attack %d %s")
        print(att_str % (self.attacking.name, self.at, _("time") if self.at == 1 else _("times")))
        print(att_str % (self.defending.name, self.dt, _("time") if self.dt == 1 else _("times")))
        self.attacking.team.play_music('battle')

        room.run_room(rooms.Fadeout(2000, stop_mixer=False))

    def anim_finished(self, tween):
        tween.go_backward(False)
        tween.callback = None
        self.show_outcome()

    def show_outcome(self):
        sounds.play(self.outcome)
        if self.outcome == 'hit':
            text = str(self.damage)
        elif self.outcome == 'critical':
            text = '%s %d' % (_(self.outcome.upper()), self.damage)
        else:
            text = _(self.outcome.upper())
        self.att_swap.animation.text.txt_color = c.RED
        if self.outcome == 'miss':
            self.att_swap.animation.text.txt_color = c.YELLOW
        self.att_swap.animation.text.set_text(text)
        self.att_swap.animation.text.visible = True
        self.att_swap.update()
        self.def_swap.update()

    def handle_mousebuttondown(self, _event: pygame.event.Event):
        if _event.button == pygame.BUTTON_LEFT:
            self.skip_round()

    def handle_keydown(self, _event: pygame.event.Event):
        if _event.key == pygame.K_SPACE:
            self.skip_round()

    def skip_round(self):
        if self.outcome:
            self.att_swap.animation.reset()
            self.show_outcome()
            self.next_round()

    def next_round(self):
        self.at -= 1
        self.round += 1
        if self.dt > 0:
            self.at, self.dt = self.dt, self.at
            self.att_swap, self.def_swap = self.def_swap, self.att_swap
        self.outcome = self.damage = None
        self.done = (self.at <= 0 and self.dt <= 0) or self.attacking.health <= 0 or self.defending.health <= 0

    def loop(self, _events, dt):
        super().loop(_events, dt)
        animation = self.att_swap.animation
        if animation.clock == 0:
            animation.playing = True
            print(f'{" " * 6}{"-" * 6}Round {self.round}{"-" * 6}')
            self.outcome, self.damage = self.att_swap.unit.attack(self.def_swap.unit)
            if self.outcome == 'critical':
                animation.easing = gui.tween.in_back
                animation.duration = 500
            else:
                animation.easing = gui.tween.linear
                animation.duration = 200
        elif animation.clock < -1000:
            animation.go_backward()
            animation.callback = self.anim_finished
            animation.text.visible = False
            animation.invalidate()
            self.next_round()

    @staticmethod
    def exp_or_die(unit1: Unit, unit2: Unit) -> None:
        if unit1.health > 0:
            unit1.gain_exp(unit2)
            room.run_room(ExperienceAnimation(unit1))
        else:
            s.loaded_map.kill_unit(unit1)

    def end(self):
        super().end()

        if self.attacking.weapon and self.attacking.weapon.uses == 0:
            broken_screen(self.attacking)
        if self.defending.weapon and self.defending.weapon.uses == 0:
            broken_screen(self.defending)

        room.run_room(rooms.Fadeout(500))

        self.attacking.team.play_music('map', True)

        self.attacking.played = True

        self.exp_or_die(self.attacking, self.defending)
        self.exp_or_die(self.defending, self.attacking)

        s.loaded_map.sprites_layer.update()

        if self.defending.team.is_defeated():
            s.winner = self.attacking.team
        elif self.attacking.team.is_defeated():
            s.winner = self.defending.team

        print("#" * 12 + " " + _("Battle ends") + " " + "#" * 12 + "\r\n")


class ExperienceAnimation(gui.LinearLayout):
    def __init__(self, _unit: Unit, **kwargs) -> None:
        super().__init__(wait=False,
                         layout=room.Layout(width=room.LayoutParams.FILL_PARENT, height=room.LayoutParams.FILL_PARENT),
                         default_child_gravity=room.Gravity.CENTER, **kwargs)
        self.unit = _unit
        self.gained_exp = _unit.exp_prev + _unit.gained_exp()
        self.image = gui.Image(_unit.image, die_when_done=False)
        self.bar = gui.LifeBar(max=99, value=_unit.exp_prev, blocks_per_row=100, block_size=(2, 10),
                               life_color=c.YELLOW)
        self.label = gui.Label(_("EXP: {experience}") + "\t" + _("LV: {level}"), f.SMALL, txt_color=c.YELLOW)
        self.label.format(**_unit.__dict__)
        self.add_children(self.image, self.bar, self.label)
        self.time = 0

    def begin(self):
        super().begin()
        sounds.play('exp', -1)
        self.bind_keys((p.K_RETURN, p.K_SPACE), self.handle_event)
        self.bind_click((1,), self.handle_event)

    def loop(self, _events, dt):
        super().loop(_events, dt)
        self.time += dt
        if self.bar.value < self.gained_exp:
            self.bar.value += 1
            if self.unit.levelled_up() and self.bar.value % 100 == 0:
                sounds.play('levelup')
            self.label.format(**self.unit.__dict__)
        else:
            if self.time > 2000:
                self.done = True
            elif self.time > 100:
                sounds.stop('exp')

    def handle_event(self, _event):
        self.bar.value = self.gained_exp


def test_battle_animation():
    display.initialize()
    import gettext
    import logging
    import resources
    gettext.install('ice-emblem', resources.LOCALE_PATH)
    logging.basicConfig(level=logging.DEBUG)
    s.load_map('resources/maps/default.tmx')
    unit1 = Unit(name='Soldier', health=30, level=1, experience=99, strength=5, skill=500, speed=1, luck=2, defence=1,
                 resistance=1, movement=1, constitution=1, aid=1, affinity=None, wrank=[])
    unit2 = Unit(name='Skeleton', health=31, level=1, experience=0, strength=6, skill=30, speed=10, luck=1, defence=1,
                 resistance=1, movement=1, constitution=1, aid=1, affinity=None, wrank=[])
    unit1.coord = (1, 1)
    unit2.coord = (1, 2)
    Team('Ones', (255, 0, 0), 0, [unit1], unit1, {})
    Team('Twos', (0, 0, 255), 0, [unit2], unit2, {})
    s.units_manager.units = [unit1, unit2]
    display.window.fill(c.GREY)
    while unit1.health > 0 and unit2.health > 0:
        room.run_room(BattleAnimation(unit1, unit2))
        unit1, unit2 = unit2, unit1
        unit1.played = unit2.played = False
    pygame.quit()


if __name__ == '__main__':
    test_battle_animation()
