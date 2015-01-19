import pygame
import os.path


class ie_unit:
	def __init__ (self, name, HP_max, HP, LV, E, Str, Skill, Spd, Luck, Def, Res, Move, Con, Aid, Trv, Affin, Cond, WRank):
		self.name	=	str(name)   	# name of the character
		self.HP_max	=	int(HP_max) 	# Maximum HP
		self.HP 	=	int(HP)     	# Current HP
		self.LV 	=	int(LV)     	# Level
		self.E  	=	int(E)      	# Experience
		self.Str	=	int(Str)    	# Strength determines the damage inflicted to the enemy
		self.Skill	=	int(Skill)  	# Skill chance of hitting the enemy
		self.Spd	=	int(Spd)    	# Speed chance to avoid enemy's attack
		self.Luck	=	int(Luck)   	# Luck influences 
		self.Def	=	int(Def)    	# Defence reduces phisical damages
		self.Res	=	int(Res)    	# Resistence reduces magical damages
		self.Move	=	int(Move)   	# Movement determines how far the unit can move in a turn
		self.Con	=	int(Con)    	# Constitution, or phisical size. Affects rescues.
		self.Aid	=	int(Aid)    	# Max rescuing constitution. Units with lower Con can be rescued.
		self.Trv	=	Trv         	# Traveler. The unit with whom this unit is traveling.
		self.Affin	=	Affin       	# Elemental Affinity. Determines compatibility with other units.
		self.Cond	=	Cond        	# Health conditions.
		self.WRank	=	WRank       	# Weapons' Levels.
		self.Items	=	[]          	# List of items
		self.played	=	False       	# Wether unit was used or not
		path = os.path.abspath(self.name + '.png')
		try:
			self.image	=	pygame.image.load(path).convert_alpha()
		except pygame.error, e:
			print("Couldn't load " + path)
			print(e)
			self.image = None
	def __str__ (self):
		return """
Unit: "%s"
	HP: %d/%d
	LV: %d E: %d
	Str: %d
	Skill: %d
	Spd: %d
	Luck: %d
	Def: %d
	Res: %d
	Move: %d
	Con: %d
"""% (self.name,  # TODO: Not yet complete
			self.HP, self.HP_max, self.LV, self.E, self.Str,
			self.Skill, self.Spd, self.Luck, self.Def,
			self.Res, self.Move, self.Con)

	def getActiveWeapon (self):
		"""Returns the active weapon if it exists, None otherwise."""
		for item in self.Items:
			if item.active:
				return item
		return None

	def giveWeapon (self, weapon, active=True):
		"""Gives a weapon to the unit. The weapon becomes active by default."""
		weapon.active = active
		self.Items.append(weapon)

	def inflictDamage (self, dmg):
		"""Inflicts damages to the unit."""
		self.HP -= dmg
		if self.HP <= 0:
			self.HP = 0
			print("%s died"% self.name)
