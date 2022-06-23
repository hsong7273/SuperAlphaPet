#
from shop import Shop

class Game():
	def __init__(self, config) -> None:
		# 
		if config:
			self.turn = config.turn
			self.team = config.team
			self.health = config.health
			self.wins = config.wins
		else: # Start from scratch
			self.turn = 1
			self.team = [] #Empty Team object?
			self.health = 10
			self.wins = 0


		pass

	def buypet(self, target, destination, level=False):
		pass
	def movepet(self, target, destination, level=False):
		pass
	def sellpet(self, target):
		pass
	def freezeitem(self, target):
		pass
	def reroll(self):
		pass
	def endturn(self):
		pass
	def legelactions(self, shop):
		pass
	def evaluate(self):
		pass
	def statevector(self):
		sv = []
		return sv
	def executeaction(self, a_ind):
		# choose execute action function
		if a_ind==159:
			self.endturn()
		pass








