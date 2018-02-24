class Action(object):
	def __init__(self):
		pass

class Attack(Action):
	def __init__(self, attacking, defending):
		self.defending = defending
		self.attacking = attacking

	def __call__(self):
		self.fun(self.attacking, self.defending)

	def __str__(self):
		return f"{self.attacking.name} vs {self.defending.name}"


class Move(Action):
	def __init__(self, who, where):
		self.who = who
		self.where = where

	def __call__(self):
		self.fun(self.who, self.where)

	def __str__(self):
		return f"Move {self.who.name} to {self.where}"
