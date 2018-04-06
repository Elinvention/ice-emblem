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
        super().__init__(vector, 200, callback=on_animation_finished, bg_color=(0, 0, 0, 0), children=[image])
        self.drawn = False

    def loop(self, _events, dt):
        self.drawn = False
        return super().loop(_events, dt)

    def draw(self, surface=display.window):
        if self.root and not self.drawn:
            self.drawn = True
            self.parent.parent.draw()
        else:
            super().draw(surface)


class BattleUnitStats(gui.Container):
    def __init__(self, unit, vector, on_animation_finished, **kwargs):
        super().__init__(bg_color=(0, 0, 0, 0), **kwargs)
        self.unit = unit
        self.animation = AttackAnimation(gui.Image(unit.image), vector, on_animation_finished)
        self.name = gui.Label(unit.name, f.MAIN, txt_color=unit.team.color, bg_color=(0, 0, 0, 0))
        self.life = gui.LifeBar(max=unit.health_max, value=unit.health)
        self.stats = gui.Label(str(unit), f.SMALL, bg_color=(0, 0, 0, 0))
        self.add_children(self.animation, self.name, self.life, self.stats)

    def update(self):
        self.life.value = self.unit.health
        self.stats.set_text(str(self.unit))


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
        self.bar.value += 1
        if self.unit.levelled_up() and self.bar.value == 100:
            sounds.play('levelup')
        self.label.format(**self.unit.__dict__)
        return self.bar.value > self.gained_exp

    def handle_mousebuttondown(self, event):
        self.bar.value = self.gained_exp

    def handle_keydown(self, event):
        self.bar.value = self.gained_exp

    def draw(self, surface=display.window):
        display.window.fill(c.BLACK)
        display.window.blit(battle_background, (0, 0))
        super().draw()

    def end(self):
        sounds.stop('exp')
        self.wait_event(timeout=2000)


class BattleAnimation(room.Room):
    def __init__(self, attacking, defending, **kwargs):
        super().__init__(wait=False, fps=1, **kwargs)
        self.attacking = attacking
        self.defending = defending
        drect = display.get_rect()
        self.att_stats = self.att_swap = BattleUnitStats(self.attacking, (50, 0), self.anim_finished, center=(drect.centerx-drect.centerx//2, drect.centery))
        self.def_stats = self.def_swap = BattleUnitStats(self.defending, (-50, 0), self.anim_finished, center=(drect.centerx+drect.centerx//2, drect.centery))
        self.add_children(self.att_stats, self.def_stats)

    def begin(self):
        global battle_background
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

        s.loaded_map.draw(display.window)
        room.run_room(rooms.Fadeout(1000))  # Darker atmosphere
        battle_background = display.window.copy()

    def anim_finished(self, tween):
        tween.go_backward()
        tween.callback = None
        outcome = self.att_swap.unit.attack(self.def_swap.unit)
        self.def_swap.update()
        sounds.play(outcome)
        """
        TODO:
        miss_text = f.SMALL.render(_("MISS"), 1, c.YELLOW).convert_alpha()
        null_text = f.SMALL.render(_("NULL"), 1, c.RED).convert_alpha()
        crit_text = f.SMALL.render(_("TRIPLE"), 1, c.RED).convert_alpha()
        """

    def loop(self, _events, dt):
        print(f'{" " * 6}{"-" * 6}Round {self.round}{"-" * 6}')
        display.clock.tick(60)
        room.run_room(self.att_swap.animation)
        self.at -= 1
        if self.dt > 0:
            self.round += 1
            self.at, self.dt = self.dt, self.at
            self.att_swap, self.def_swap = self.def_swap, self.att_swap
        return (self.at <= 0 and self.dt <= 0) or self.attacking.health <= 0 or self.defending.health <= 0

    def draw(self, surface=display.window):
        surface.fill(c.BLACK)
        surface.blit(battle_background, (0, 0))
        super().draw(surface)

    def exp_or_die(self, unit1, unit2):
        if unit1.health > 0:
            unit1.gain_exp(unit2)
            room.run_room(ExperienceAnimation(unit1, center=display.get_rect().center))
        else:
            s.kill(unit1)

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

        display.window.blit(battle_background, (0, 0))
        self.attacking.played = True

        if self.defending.team.is_defeated():
            s.winner = self.attacking.team
        elif self.attacking.team.is_defeated():
            s.winner = self.defending.team

        self.exp_or_die(self.attacking, self.defending)
        self.exp_or_die(self.defending, self.attacking)

        print("#" * 12 + " " + _("Battle ends") + " " + "#" * 12 + "\r\n")
