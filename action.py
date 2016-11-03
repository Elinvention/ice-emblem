class Action(object):
	def __init__(self):
		pass


class Attack(Action):
	def __init__(self, attacking, defending):
		self.defending = defending
		self.attacking = attacking

	def __call__(self):
		self.fun(self.attacking, self.defending)


class Move(Action):
	def __init__(self, who, where):
		self.who = who
		self.where = where

	def __call__(self):
		self.fun(self.who, self.where)
