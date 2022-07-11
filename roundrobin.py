import numpy as np
from sapai import Player
from sapai import Battle

def roundrobin(players: list[Player], rounds=-1):
	'''Conducts RoundRobin battles between players
	Returns winrates
	Only supports single-roundrobin
	Matchups are always done in order, players are assumed to be uncorrelated
	'''
	if rounds==-1:
		rounds = len(players)-1
	if rounds>=len(players):
		raise Exception("Only supports single-roundrobin")
	
	wins = np.zeros(len(players))
	fought = np.zeros(len(players))
	for idx, pl1 in enumerate(players[:-1]):
		# Check for empty teams
		if len(pl1.team)==0:
			continue
		round = 0
		# Battle Queue loop, 
		for jdx, pl2 in enumerate(players[idx+1:]):
			if len(pl2.team)==0: # Skip empty teams
				continue
			# Conduct Battle
			b = Battle(pl1.team, pl2.team)
			result = b.battle() # 0-pl1, 1-pl2, 2-draw
			if result==0:
				wins[idx]+=1
			elif result==1:
				wins[idx+1+jdx]+=1
			elif result==2:
				wins[idx]+=0.5
				wins[idx+1+jdx]+=0.5
			else:
				raise Exception(f"battle not over: {result}")
			
			fought[idx]+=1
			fought[idx+1+jdx]+=1
			round+=1
			if round==rounds: # If fewer fights are desired
				break
	# Calculate winrate
	fought[np.where(fought==0)[0]] = 1
	wr = wins/fought
	return wr