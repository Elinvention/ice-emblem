class ie_item:
	"""Generic item class"""
	def __init__ (self, name, descr = ""):
		self.name = name
		self.descr = descr
	def __str__ (self):
		return "Item:\r\n\tName: \"%s\"\r\n\tDescription: \"%s\""% (self.name, self.descr)

class ie_weapon (ie_item):
	"""Swords, Lances, Axes, Bows, Tomes, Staffs"""
	def __init__ (self, name, Rank, Might, Weight, Hit, Crit, Range, Uses, Worth, Exp, descr = ""):
		self.name = name
		self.descr = descr
		self.Rank	=	Rank
		self.Might	=	Might
		self.Weight	=	Weight
		self.Hit	=	Hit
		self.Crit	=	Crit
		self.Range	=	Range
		self.MUses	=	Uses
		self.Uses	=	Uses
		self.Worth	=	Worth
		self.Exp	=	Exp
		self.active	=	False
	def toggleActive (self):
		self.active = not self.active
	def use(self):
		self.Uses -= 1
		if self.Uses <= 0:
			self.Uses = 0
			print("%s is broken"% self.name)
			return False
		else:
			return True
	def __str__ (self):
		return """
Weapon "%s":
	Description: "%s"
	Rank: %c
	Might: %d
	Weight: %d
	Hit: %d
	Crit: %d
	Range: %d
	Uses: %d/%d
	Worth: %d
	Exp: %d
	active: %d
"""% (self.name, self.descr, self.Rank, self.Might, self.Weight, self.Hit, self.Crit, self.Range, self.Uses, self.MUses, self.Worth, self.Exp, self.active)

#class ie_sword (ie_weapon):
#	pass
