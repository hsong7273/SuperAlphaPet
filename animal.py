import eventnames
import numpy as np

# Base class
class Animal():
	def __init__(self):
		self.name = ""
		self.tier = 0
		self.exp = 0
		self.level = 0
		self.health = 0
		self.attack = 0

		# Maybe code these as ints later
		self.trigger = ""
		self.food = "" # Battle engine uses food to determine outcomes

		self.needs = []

	def levelup(self):
		# Check which animal placed on which, or make equivalent actions
		if self.exp==6: # Shouldn't allow this
			pass
		self.exp += 1
		self.health += 1
		self.attack += 1
		if self.exp==2:
			self.level = 2
			return eventnames.ON_LEVEL
		if self.exp==5:
			self.level = 3
			return eventnames.ON_LEVEL
		
		# Raise Level up Event
		return eventnames.ON_LEVEL

	def effect(self):
		pass

	def takedamage(self, dmg):
		#TODO: Garlic, Weakness, Coconut
		if self.food == 'melon':
			self.food = ''
			dmg = np.clip(dmg-20, 0)
			if dmg==0:
				return

		self.health -= dmg
		if self.health<=0: #faint
			return self.faint()
		else:
			return eventnames.HURT

	def faint(self):
		return eventnames.ON_FAINT


class Ant(Animal):
	def __init__(self):
		super().__init__()
		self.trigger = eventnames.ON_FAINT
		self.health = 1
		self.attack = 2
		self.level = 1
		self.exp = 0
		self.needs = ["team1"]

	# Maybe each animal has a list of needs (teams, shop, gold)
	def effect(self, team1):
		"""Faint: Give a random friend (+2/+1)/(+4/+2)/(+6/+3)."""
		
		# random remaining animal
		# Faint should have already happened, and ant removed
		pos = np.random.randint(team1.size)
		target = team1.getpos(pos)
		target.health += 1*self.level
		target.attack += 2*self.level
		team1.setpos(target)

class Mosquito(Animal):
	def __init__(self):
		super().__init__()
		self.trigger=eventnames.START_BATTLE
		self.health = 2
		self.attack = 2
		self.level = 1
		self.exp = 0
		self.needs = ["team2"]

	# Maybe each animal has a list of needs (teams, shop, gold)
	def effect(self, team2):
		"""Start of battle: Deal 1 dmg to 1/2/3 random enemies."""
		
		# random remaining animal
		# Faint should have already happened, and ant removed
		pos = np.random.randint(team2.size)
		target = team2.getpos(pos)
		event = target.takedamage(1*self.level)
		team2.setpos(target)
		return event




