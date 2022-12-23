# Generates random SAP teams, evaluates strength and saves 
import numpy as np
from sapai import *

def onehot(idx, nb_classes):
	oh = np.zeros(nb_classes)
	if idx==-1:
		return oh
	oh[idx] = 1
	return oh

class TeamStateBuilder():
	"""Class for building team state vector
	Pre-indexes game items
	team_state method converts given team to team_state vector
	"""
	def __init__(self, pack="StandardPack"):

		self.pack = pack
		# Count pets/foods/statuses in pack, for state vector
		nPets = 0
		nFoods = 0
		nStatuses = 0
		# Lookup of Pet, Food, Status index
		self.petDict = {}
		self.foodDict = {}
		self.statusDict = {}
		for p in data['pets'].values():
			if self.pack in p['packs']:
				self.petDict[p['id']] = nPets
				nPets += 1
		for f in data['foods'].values():
			if self.pack in f['packs']:
				self.foodDict[f['id']] = nFoods
				nFoods += 1
		for s in data['statuses'].values():
			self.statusDict[s['id']] = nStatuses
			nStatuses += 1
		self.nPets = nPets
		self.nFoods = nFoods
		self.nStatuses = nStatuses
		# Calculate vector size and fields from game information
		self.state_length = self._max_team*(self.nPets+self.nStatuses+3) # Team state
		self.state_length += self._max_shop*(self.nPets+4)+2*(self.nFoods+2) # shop state(pets/food/costs)
		self.state_length += 4 # gold/lives/wins/turn
		# Count total actions for agent
		# Move, Move+LevelUp
		self.action_length = 2*self._max_team*(self._max_team-1)
		# BUYPET-PLACE, BUYPET-LEVEUP, Sell
		self.action_length += 2*self._max_shop*self._max_team+self._max_team
		# BUY FOOD, FREEZE/UNFREEZE, ROLL, END TURN
		self.action_length += 2*self._max_team+2+14+2


	def team_state(self, team):
		state_v = np.array([])
		# Parse team information
		for idx, ts in enumerate(team):
			if ts.pet.name=='pet-none':
				state_v = np.concatenate((state_v, np.zeros(self.nPets+3+self.nStatuses)))
			else:
				# Pet state
				petid = self.petDict[ts.pet.name]
				pet_v = onehot(petid, self.nPets)
				stat_v = [ts.pet.attack/50.,ts.pet.health/50.,ts.pet.experience+1]
				# Pet Statuses
				if ts.pet.status=='none':
					status_v = onehot(-1, self.nStatuses)
				else:
					statusid = self.statusDict[ts.pet.status]
					status_v = onehot(statusid, self.nStatuses)
				pet_v = np.concatenate((pet_v, stat_v, status_v))
				state_v = np.concatenate((state_v, pet_v))
		return state_v

