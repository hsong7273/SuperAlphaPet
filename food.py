import eventnames
from animal import *

# Base Class
class Food():
	def __init__(self):
		self.cost = 0
		self.tier = 0
		self.needs = []
		self.trigger = ''
		self.frozen = False

	def effect(self):
		pass

class Apple(Food):
	def __init__(self):
		# Food specific information
		self.cost = 3
		self.tier = 1
		self.needs = ["target"]
	def effect(self, target):
		target.health += 1
		target.attack += 1

class Honey(Food):
	def __init__(self):
		# Food specific information
		self.cost = 3
		self.tier = 1
		self.trigger = eventnames.ON_FAINT
		self.needs = ["team"]
	def effect(self, team):
		team.append(Bee())