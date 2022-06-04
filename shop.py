from animal import *
from food import *
import numpy as np

# Constants
#Standard Pack
pets_in_tiers = [9, 10, 11, 11, 8, 9]
foods_in_tiers = [2,3,2,2,3,4]
pet_size = {
			1:3,
			2:3,
			3:4,
			4:4,
			5:5,
			6:5,
			}
food_size = {
			1:1,
			2:1,
			3:2,
			4:2,
			5:2,
			6:2,
			}
PETS = []
FOODS = []
class Shop():
	# initialized at each turn
	def __init__(self, turn, frozen):
		self.frozen = frozen
		self.n_animals = 0
		self.n_food = 0
		# to be filled by rolling
		self.animals = []
		self.foods = []

		# Based on turn
		self.tier = np.clip(int((turn-1)/2)+1,1,6)
		self.n_animals = pet_size[self.tier]
		self.n_food = food_size[self.tier]
		
		self.avail_pets = sum(pets_in_tiers[:self.tier])
		self.avail_foods = sum(foods_in_tiers[:self.tier])

		self.roll()
	# Should shop roll or game roll (re-init shop?)
	def roll(self):
		# roll for each slot, pet then food
		for i in range(self.n_animals):
			if self.animals[i].frozen:
				continue
			# Choose pet and initialize
			idx = np.randint(self.avail_pets)
			self.animals[i] = PETS[idx]()
			#TODO: Canned food / Chicken Effects

		for i in range(self.n_food):
			if self.foods[i].frozen:
				continue
			# Choose food and initialize
			idx = np.randint(self.avail_foods)
			self.foods[i] = FOODS[idx]()

			


		pass

	def boost(self):
		""" When a pet levels up, offer random pet from next tier
		"""
		if len(self.animals)==5: # Shop is full
			return
		
		# Choose highest available tier pet
		target_tier = np.clip(self.tier+1,1,6)
		avail_pets = pets_in_tiers[target_tier-1]
		N_low_pets = sum(pets_in_tiers[:target_tier])
		new_pet = PETS[N_low_pets+np.randint(avail_pets)]()
		self.animal.append(new_pet)


