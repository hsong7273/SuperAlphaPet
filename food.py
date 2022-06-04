# Base Class
class Food():
	def __init__(self):
		self.cost = 0
		self.tier = 0
		self.needs = []

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