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


class AttackAnimation(gui.Tween):
    def __init__(self, image, vector, on_animation_finished):
        super().__init__(vector, 200, callback=on_animation_finished, die_when_done=False,
                         bg_color=(0, 0, 0, 0))
        self.text = gui.Label("", f.SMALL, visible=False, alpha=True, bg_color=(0, 0, 0, 0))
        self.add_children(self.text, image)


class BattleUnitStats(gui.Container):
    def __init__(self, unit, vector, on_animation_finished, **kwargs):
        super().__init__(padding=100, **kwargs)
        self.unit = unit
        self.animation = AttackAnimation(gui.Image(unit.image), vector, on_animation_finished)
        self.name = gui.Label(unit.name, f.MAIN, txt_color=unit.team.color, bg_color=(0, 0, 0, 0))
        self.life = gui.LifeBar(max=unit.health_max, value=unit.health)
        self.stats = gui.Label(str(unit), f.SMALL, bg_color=(0, 0, 0, 0))
        self.add_children(self.animation, self.name, self.life, self.stats)

    def update(self):
        self.life.value = self.unit.health
        self.stats.set_text(str(self.unit))


class BattleAnimation(room.Room):
    def __init__(self, attacking, defending, **kwargs):
        super().__init__(wait=False, size=display.get_size(), **kwargs)
        self.attacking = attacking
        self.defending = defending
        drect = display.get_rect()
        self.att_stats = self.att_swap = BattleUnitStats(self.attacking, (50, 0), self.anim_finished, center=(drect.centerx-drect.centerx//2, drect.centery), bg_color=c.BLACK)
        self.def_stats = self.def_swap = BattleUnitStats(self.defending, (-50, 0), self.anim_finished, center=(drect.centerx+drect.centerx//2, drect.centery), bg_color=c.BLACK)
        self.add_children(self.att_stats, self.def_stats)

    def begin(self):
        super().begin()
        self.attacking.prepare_battle()
        self.defending.prepare_battle()

        self.at, self.dt = self.attacking.number_of_attacks(self.defending)
        self.round = 1

        print(f"\r\n{'#' * 12} {self.attacking.name} vs {self.defending.name} {'#' * 12}")
        att_str = _("%s is going to attack %d %s")
        print(att_str % (self.attacking.name, self.at, _("time") if self.at == 1 else _("times")))
        print(att_str % (self.defending.name, self.dt, _("time") if self.dt == 1 else _("times")))
        self.attacking.team.play_music('battle')

        room.run_room(rooms.Fadeout(1000, stop_mixer=False))

    def anim_finished(self, tween):
        left = tween.rect.left
        tween.go_backward(False)
        tween.callback = None
        sounds.play(self.outcome)
        if self.outcome == 'hit':
            text = str(self.damage)
        elif self.outcome == 'critical':
            text = '%s %d' % (_(self.outcome.upper()), self.damage)
        else:
            text = _(self.outcome.upper())
        tween.text.txt_color = c.RED
        if self.outcome == 'miss':
            tween.text.txt_color = c.YELLOW
        tween.text.set_text(text)
        tween.text.visible = True
        self.att_swap.update()
        self.def_swap.update()
        tween.rect.left = left  # Container may reflow this child

    def loop(self, _events, dt):
        super().loop(_events, dt)
        animation = self.att_swap.animation
        if animation.clock == 0:
            animation.playing = True
            print(f'{" " * 6}{"-" * 6}Round {self.round}{"-" * 6}')
            self.outcome, self.damage = self.att_swap.unit.attack(self.def_swap.unit)
            if self.outcome == 'critical':
                animation.easing = gui.tween.inBack
                animation.duration = 500
            else:
                animation.easing = gui.tween.linear
                animation.duration = 200
        elif animation.clock < -1000:
            animation.go_backward()
            animation.reset()
            animation.callback = self.anim_finished
            animation.text.visible = False
            self.at -= 1
            self.round += 1
            if self.dt > 0:
                self.at, self.dt = self.dt, self.at
                self.att_swap, self.def_swap = self.def_swap, self.att_swap
            self.done = (self.at <= 0 and self.dt <= 0) or self.attacking.health <= 0 or self.defending.health <= 0

    def exp_or_die(self, unit1, unit2):
        if unit1.health > 0:
            unit1.gain_exp(unit2)
            room.run_room(ExperienceAnimation(unit1, center=display.get_rect().center))
        else:
            s.loaded_map.kill_unit(unit1)

    def broken_screen(self, unit):
        sounds.play('broke')
        broken_text = f.SMALL.render("%s is broken" % unit.weapon.name, True, c.RED)
        display.window.blit(broken_text, center=broken_text.get_rect().center)
        display.flip()
        self.wait_event(timeout=3000)

    def end(self):
        super().end()

        if self.attacking.weapon and self.attacking.weapon.uses == 0:
            self.broken_screen(self.attacking)
        if self.defending.weapon and self.defending.weapon.uses == 0:
            self.broken_screen(self.defending)

        pygame.mixer.music.fadeout(500)
        self.wait_event(500)
        self.attacking.team.play_music('map', True)

        self.attacking.played = True

        self.exp_or_die(self.attacking, self.defending)
        self.exp_or_die(self.defending, self.attacking)

        s.loaded_map.sprites.update()

        if self.defending.team.is_defeated():
            s.winner = self.attacking.team
        elif self.attacking.team.is_defeated():
            s.winner = self.defending.team

        print("#" * 12 + " " + _("Battle ends") + " " + "#" * 12 + "\r\n")


class ExperienceAnimation(gui.Container):
    def __init__(self, unit, **kwargs):
        super().__init__(bg_color=(0, 0, 0, 0), wait=False, allowed_events=[p.MOUSEBUTTONDOWN, p.KEYDOWN], **kwargs)
        self.unit = unit
        self.gained_exp = unit.gained_exp()
        self.image = gui.Image(unit.image)
        self.bar = gui.LifeBar(max=99, value=unit.prev_exp, blocks_per_row=100, block_size=(2, 10), life_color=c.YELLOW)
        self.label = gui.Label(_("EXP: {experience}") + "\t" + _("LV: {level}"), f.SMALL, txt_color=c.YELLOW)
        self.label.format(**unit.__dict__)
        self.add_children(self.image, self.bar, self.label)

    def begin(self):
        super().begin()
        sounds.play('exp', -1)

    def loop(self, _events, dt):
        super().loop(_events, dt)
        self.bar.value += 1
        if self.unit.levelled_up() and self.bar.value % 100 == 0:
            sounds.play('levelup')
        self.label.format(**self.unit.__dict__)
        self.done = self.bar.value >= self.gained_exp

    def handle_mousebuttondown(self, event):
        self.bar.value = self.gained_exp

    def handle_keydown(self, event):
        self.bar.value = self.gained_exp

    def end(self):
        super().end()
        sounds.stop('exp')
        self.wait_event(timeout=2000)


if __name__ == '__main__':
    import gettext, logging
    import unit, resources
    gettext.install('ice-emblem', resources.LOCALE_PATH)
    logging.basicConfig(level=20)
    s.load_map('resources/maps/default.tmx')
    unit1 = unit.Unit(name='Soldier', health=30, level=1, experience=99, strength=5, skill=500, speed=1, luck=2, defence=1, resistence=1, movement=1, constitution=1, aid=1, affinity=None, condition=None, wrank=[])
    unit2 = unit.Unit(name='Skeleton', health=31, level=1, experience=0, strength=6, skill=30, speed=10, luck=1, defence=1, resistence=1, movement=1, constitution=1, aid=1, affinity=None, condition=None, wrank=[])
    unit1.coord = (1, 1)
    unit2.coord = (1, 2)
    team1 = unit.Team('Ones', (255, 0, 0), 0, [unit1], unit1, {})
    team2 = unit.Team('Twos', (0, 0, 255), 0, [unit2], unit2, {})
    s.units_manager.units = [unit1, unit2]
    while unit1.health > 0 and unit2.health > 0:
        room.run_room(BattleAnimation(unit1, unit2))
        unit1, unit2 = unit2, unit1
