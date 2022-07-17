import numpy as np
import matplotlib.pyplot as plt
import random
from sapai import *
from roundrobin import *

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
print("DEVICE:", DEVICE)

class FCN(nn.Module):
	'''Simple 4-layer Neural Network, with non linear activation'''
	def __init__(self, n_input, n_output):
		super().__init__()
		self.fc1 = 500
		self.fc2 = 300
		self.fc3 = 500

		self.FC1 = nn.Linear(n_input, self.fc1)
		self.FC2 = nn.Linear(self.fc1, self.fc2)
		self.FC3 = nn.Linear(self.fc2, self.fc3)
		self.FC4 = nn.Linear(self.fc3, n_output)
		self.relu = nn.ReLU()

	def forward(self, x):
		x = self.FC1(x)
		x = self.relu(x)
		x = self.FC2(x)
		x = self.relu(x)
		x = self.FC3(x)
		x = self.relu(x)
		x = self.FC4(x)
		return x


class Memory(Dataset):
	'''Class that stores game memories and provides random subsets for training'''
	def __init__(self, transitions:list):
		# Maybe read from pickle file in Dataset
		self.transitions = transitions
		self.dsize = len(transitions)
		# Shuffle in place
		random.shuffle(self.transitions)

	def __len__(self):
		return self.dsize

	def __getitem__(self, idx):
		memory = self.transitions[idx]
		state = memory[0]
		action = memory[1]
		next_state = memory[2]
		reward = memory[3]
		return state, action, next_state, reward

	def sample(self, batch_size):
		'''Generator function that yields batch_size memories'''
		idx = 0
		while idx<len(self):
			batch = self.transitions[idx:idx+batch_size]
			#transpose batch
			batch_t = [list(i) for i in zip(*batch)]
			yield batch_t
			idx += batch_size


class ShopPhase_Turn1():
	'''Class for AI to play SAP-Turn 1
	manages multiple players
	uses ML model to make decisions
	stores game situations-decisions as memories
	'''
	def __init__(self, N_players, model: nn.Module):
		self.max_actions = 20
		self.model = model.to(DEVICE)

		# Initialize players
		self.players = [Player() for i in range(N_players)]

		# Initalize Memory Bank
		self.memories = []

	def shop(self, player: Player, epsilon):
		'''Takes shop actions for player until max_actions or end turn
		returns state before end_turn
		'''
		self.model.eval()
		
		with torch.no_grad():
			# Shop-Action Loop
			actions = 0
			while True: # Until Turn is ended
				# State before action
				state_0 = player.state_vector
				state = torch.from_numpy(state_0).to(DEVICE).float()
				# Calculate Q(s,a), and mask legal actions
				action_scores = self.model(state)
				legal = torch.from_numpy(player.legal_actions).to(DEVICE)
				illegal = torch.where(legal==0, 1, 0)

				action_scores = torch.add(-999*illegal, action_scores)

				# Epsilon Greedy Policy
				rand_i = np.random.rand()
				if rand_i>epsilon: # Exploit
					action_idx = torch.argmax(action_scores).item()
				elif rand_i<=epsilon: # Explore
					# Select Random Legal Action
					action_idx = int(np.random.choice(player.legal_actions.nonzero()[0]))
				# Execute action
				player.execute(action_idx)

				actions += 1
				# Don't save memory if turn ended
				if action_idx==142:
					return state_0
				if actions==self.max_actions:
					# If max_actions, save last memory and end turn
					memory = [state_0, action_idx, player.state_vector, 0]
					self.memories.append(memory)
					state_0 = player.state_vector
					player.end_turn()
					return state_0

				# Save non-endturn memory
				memory = [state_0, action_idx, player.state_vector, 0]
				self.memories.append(memory)

	def turn(self, epsilon=0.1):
		state_0 = []
		self.memories = []
		
		# metrics
		self.teamsize = []
		self.teamattack = []
		for pl in self.players:
			# shop returns last state before end_turn
			last_state = self.shop(pl, epsilon=epsilon)
			state_0.append(last_state)
			# metrics
			self.teamsize.append(len(pl.team))
			attacks = []
			for ts in pl.team:
				if type(ts.pet.attack)==int:
					attacks.append(ts.pet.attack)
			self.teamattack.append(sum(attacks))

		# Round Robin Battle
		self.rates = roundrobin(self.players)

		for idx, (pl, wr) in enumerate(zip(self.players, self.rates)):
			# Calculate lives and rewards
			if wr<0.4: #LOSE
				reward = wr
			elif 0.4<=wr<0.6: #DRAW
				reward = wr+0.5
			elif 0.6<=wr: #WIN
				reward = wr+1
			# Save terminal memory with result, no start_turn needed
			# Last action will have been end_turn
			memory = [state_0[idx], 142, None, reward]
			self.memories.append(memory)


class ModelTrainer():
	'''DQN: trains model handles dataloader, loss, optimizers'''
	def __init__(self, model:nn.Module, t_model:nn.Module, criterion=nn.MSELoss, optimizer=optim.SGD):
		# Load onto device
		model = model.to(DEVICE)
		t_model = t_model.to(DEVICE)
		# Constants
		self.BATCH=100
		self.gamma = 0.9

		# Chosen Loss Function
		self.criterion = criterion().to(DEVICE)
		self.optimizer = optimizer(model.parameters(), lr=0.1, momentum=0.9)

		# Metrics
		self.losses = []
		self.rewards = []
		self.values = []

	def train(self, model, t_model, memories, Nepochs=1):
		'''Training Loop over memories
		'''
		# Make Dataset and DataLoader
		memory = Memory(memories)

		model.train()
		self.losess = []
		for epoch in range(Nepochs):
			# Initialize random memory batch generator
			loader = memory.sample(self.BATCH)
			loss_i = 0
			# Loop over training memories
			while True:
				try: # Get batch of memories from dataset
					mems = next(loader)
				except StopIteration:
					# Stop when no more memories
					break
				# Checks for loss calculation
				terminal = False
				intermediate = False

				# Select Terminal memories
				f_ind = [i for i in range(len(mems[0])) if type(mems[2][i])!=np.ndarray]
				s = np.array([mems[0][i] for i in f_ind])
				a = np.array([mems[1][i] for i in f_ind])
				r = np.array([mems[3][i] for i in f_ind])
				if len(s)!=0: # Train with final memories
					terminal = True
					s = torch.Tensor(s).to(DEVICE).float()
					a = torch.Tensor(a).to(DEVICE).type(torch.int64)
					r = torch.Tensor(r).to(DEVICE)
					# Reevaluate action scores
					act_s = model(s)
					# Chosen action-values
					Q_a = act_s.gather(1, a.view(-1,1)).flatten()
					# Calculate target values
					with torch.no_grad():
						# Don't need to "look-ahead past final state"
						y = r
					# Calculate Loss	
					loss = self.criterion(Q_a, y)

				# Select non-terminal memories
				f_ind = [i for i in range(len(mems[0])) if type(mems[2][i])==np.ndarray]
				s = np.array([mems[0][i] for i in f_ind])
				a = np.array([mems[1][i] for i in f_ind])
				n = np.array([mems[2][i] for i in f_ind])
				r = np.array([mems[3][i] for i in f_ind])
				if len(s)!=0:
					intermediate = True
					# Train with non-terminal memories
					s = torch.Tensor(s).to(DEVICE).float()
					a = torch.Tensor(a).to(DEVICE).type(torch.int64)
					n = torch.Tensor(n).to(DEVICE).float()
					r = torch.Tensor(r).to(DEVICE)
					# Reevaluate action scores
					act_s = model(s)
					# Chosen action-values
					Q_a = act_s.gather(1, a.view(-1,1)).flatten()
					# Calculate target values with target model
					Q_f = t_model(n).max(1)[0].detach()
					y = r+self.gamma*Q_f
					# Calculate Loss
					if terminal:
						loss = loss + self.criterion(Q_a, y)
					else:
						loss = self.criterion(Q_a, y)
				loss_i += loss.item()

				# Optimize model
				self.optimizer.zero_grad()
				loss.backward()
				self.optimizer.step()
			# Save losses for metrics
			self.losses.append(loss_i)
			# Copy parameters to target network
			t_model.load_state_dict(model.state_dict())


if __name__=='__main__':
	'''Example of how model is trained on Super Auto Pets Turn 1'''
	
	# initialize model to appropriate size for player
	pl = Player()
	model = FCN(pl.state_length, pl.action_length)
	t_model = FCN(pl.state_length, pl.action_length)

	# Prepare 10 teams in ShopPhase
	shopphase = ShopPhase_Turn1(10, model)
	shopphase.turn()

	# Print first 3 teams made by AI
	for i in range(3):
		print(shopphase.players[i].team)

	# Train model with memories of shopphase
	mt = ModelTrainer(model)
	transitions = shopphase.memories
	mt.train(model, t_model, transitions)
