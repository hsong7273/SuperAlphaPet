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

	def buypet(target, destination, level=False):
		pass
	def movepet(target, destination, level=False):
		pass
	def sellpet(target):
		pass
	def freezeitem(target):
		pass
	def reroll():
		pass
	def endturn():
		pass
	def legelactions(shop):
		pass
	def evaluate():
		pass
	def statevector():
		sv = []
		return sv
	def executeaction(a_ind):
		pass








