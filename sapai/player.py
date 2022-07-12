
import numpy as np
from sapai import data
from sapai.battle import Battle
from sapai.effects import RespawnPet, SummonPet, SummonRandomPet, get_effect_function, get_target

import sapai.shop
from sapai.shop import Shop
from sapai.teams import Team,TeamSlot

def onehot(idx, nb_classes):
    oh = np.zeros(nb_classes)
    if idx==-1:
        return oh
    oh[idx] = 1
    return oh

def targeted_food(food):
    name = food.name
    targeted = ["food-apple", 
                "food-honey", 
                "food-cupcake",
                "food-meat-bone",
                "food-sleeping-pill",
                "food-garlic",
                "food-pear",
                "food-chili",
                "food-chocolate",
                "food-melon",
                "food-mushroom",
                "food-steak",
                "food-milk"
                ]
    team = ["food-salad-bowl",
            "food-canned-food",
            "food-sushi",
            "food-pizza",
            ]
    if name in targeted:
        return True
    elif name in team:
        return False
    else:
        raise Exception("Food unknown to f:targeted_food")

def storeaction(func):
    def store_action(*args, **kwargs):
        player = args[0]
        action_name = str(func.__name__).split(".")[-1]
        targets = func(*args,**kwargs)
        store_targets = []
        if targets != None:
            for entry in targets:
                if getattr(entry, "state", False):
                    store_targets.append(entry.state)
        player.action_history.append((action_name, store_targets))
        
    ### Make sure that the func returned as the same name as input func
    store_action.__name__ = func.__name__
    
    return store_action


class Player():
    """
    Defines and implements all of the actions that a player can take. In particular
    each of these actions is directly tied to the actions reinforment learning 
    models can take. 
    
    Actions with the shop are based off of Objects and not based off of indices. 
    There is a huge advantage to doing things this way. The index that a Pet/Food 
    is in a shop is arbitrary. Therefore, when actions are based off the Object,
    The ML Agent will not have to learn the index invariances of the shop.
    
    The Player class is allowed to make appropriate changes to the Shop and 
    Team. Therefore, Shops and Teams input into the Player class will not be
    static. The Player class is also responsible for checking all of the 
    relevant Pet triggers when taking any action. 
    
    """
    def __init__(self, 
                 shop=None, 
                 team=None, 
                 lives=10, 
                 default_gold=10,
                 gold=10, 
                 turn=1,
                 lf_winner=None,
                 action_history=[],
                 pack="StandardPack",
                 seed_state=None,
                 wins=0):
        self.shop = shop
        self.team = team
        self.lives = lives
        self.default_gold = default_gold
        self.gold = gold
        self.pack = pack
        self.turn = turn
        self.wins = wins
        
        ### Default Parameters
        self._max_team = 5
        self._max_shop = 7
        
        ### Keep track of outcome of last battle for snail
        self.lf_winner = lf_winner
        
        ### Initialize shop and team if not provided
        if self.shop == None:
            self.shop = Shop(pack=self.pack,seed_state=seed_state, turn=self.turn)
        if self.team == None:
            self.team = Team(seed_state=seed_state)
        
        if type(self.shop) == list:
            self.shop = Shop(self.shop,seed_state=seed_state)
        if type(self.team) == list:
            self.team = Team(self.team,seed_state=seed_state)

        ### Connect objects
        self.team.player = self
        for slot in self.team:
            slot._pet.player = self
            slot._pet.shop = self.shop
        
        for slot in self.shop:
            slot.item.player = self
            slot.item.shop = self.shop
        
        ### This stores the history of actions taken by the given player
        if len(action_history) == 0:
            self.action_history = []
        else:
            self.action_history = list(action_history)

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
        
    @property
    def team_state(self):
        '''State vector for team only, for team-value networks'''
        state_v = np.array([])
        # Parse team information
        for idx, ts in enumerate(self.team):
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

    @property
    def state_vector(self):
        ### converts game state into state vector for AI
        state_v = np.array([])

        # Parse team information
        for idx, ts in enumerate(self.team):
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

        # Parse shop information
        n_pets = 0
        n_foods = 0
        petpadded = False
        for idx, slot in enumerate(self.shop):
            if slot.slot_type=="pet" or slot.slot_type=="levelup": # upto 7 pet slots
                # Deal with pet-none
                if slot.item.name=='pet-none':
                    state_v = np.concatenate((state_v, np.zeros(self.nPets+4)))
                    n_pets+=1
                    continue
                petid = self.petDict[slot.item.name]
                slot_v = onehot(petid, self.nPets)
                stat_v = [slot.item.attack/50., slot.item.health/50., slot.cost, slot.frozen*1]
                slot_v = np.concatenate((slot_v, stat_v))
                state_v = np.concatenate((state_v, slot_v))
                n_pets +=1

            if slot.slot_type=="food": # upto 2 food slots
                if n_pets<7 and not petpadded: # pad state vector with empty pet slots
                    state_v = np.concatenate((state_v, np.zeros((7-n_pets)*(self.nPets+4))))
                    petpadded = True
                if slot.item.name=='food-none':
                    state_v = np.concatenate((state_v, np.zeros(self.nFoods+2)))
                    n_foods += 1
                    continue

                foodid = self.foodDict[slot.item.name]
                food_v = onehot(foodid, self.nFoods)
                state_v = np.concatenate((state_v, food_v, [slot.cost, 1*slot.frozen]))
                n_foods += 1 # how many foods so far in shop (1,2)
        # zero-pad if less than 2 foods in shop
        state_v = np.concatenate((state_v, np.zeros((2-n_foods)*(self.nFoods+2))))

        # Game State
        game_state = [self.turn, self.wins, self.lives, self.gold]
        state_v = np.concatenate((state_v, game_state))
        if len(state_v) != self.state_length:
            raise Exception(f"Wrong state vector size, {len(state_v)}, not {self.state_length}")
        return state_v

    @property
    def legal_actions(self):
        '''mask array of legal action_idx'''
        legal_v = np.array([])
        # MOVE 5*4=20
        for idx, ts in enumerate(self.team):
            if ts.pet.name=='pet-none':
                legal_v = np.concatenate((legal_v, np.zeros(self._max_team-1)))
            else:
                legal_v = np.concatenate((legal_v, np.ones(self._max_team-1)))

        # MOVE-LEVELUP 5*4=20
        for idx, ts in enumerate(self.team):
            if ts.pet.name=='pet-none':
                legal_v = np.concatenate((legal_v, np.zeros(self._max_team-1)))
                continue
            if ts.pet.level==3:
                legal_v = np.concatenate((legal_v, np.zeros(self._max_team-1)))
                continue
            # check friends
            target = ts.pet.name
            friends = [i for i in range(self._max_team) if i!=idx]
            cancombine = np.zeros(self._max_team-1)
            for idx, f in enumerate(friends):
                f_pet = self.team[f].pet
                if f_pet.name==target and f_pet.experience!=3:
                    cancombine[idx] = 1
            legal_v = np.concatenate((legal_v, cancombine))
        
        # BUYPET-PLACE 7*5=35
        # Check team full
        if len(self.team)==self._max_team:
            legal_v = np.concatenate((legal_v, 7*np.zeros(5)))
        # if not full, new pet can be placed anywhere, team will shift
        else:
            for idx, slot in enumerate(self.shop):
                if slot.slot_type!="pet" or slot.cost>self.gold:
                    legal_v = np.concatenate((legal_v, np.zeros(5)))
                elif slot.item.name=='pet-none':
                    legal_v = np.concatenate((legal_v, np.zeros(5)))
                else:
                    legal_v = np.concatenate((legal_v, np.ones(5)))
            legal_v = np.concatenate((legal_v, np.zeros(5*(7-len(self.shop)))))

        # BUYPET-LEVELUP 7*5=35
        if len(self.team)==0: #empty team
            legal_v = np.concatenate((legal_v, np.zeros(35)))
        else:
            for idx, slot in enumerate(self.shop):
                if slot.slot_type!="pet" or slot.cost>self.gold:
                    legal_v = np.concatenate((legal_v, np.zeros(5)))
                    continue
                if slot.item.name=='pet-none':
                    legal_v = np.concatenate((legal_v, np.zeros(5)))
                    continue
                target = slot.item.name
                # if affordable pet, check team
                buyable = np.zeros(5)
                for idx, ts in enumerate(self.team):
                    if ts.pet.name==target and ts.pet.level<3:
                        buyable[idx] = 1
                legal_v = np.concatenate((legal_v, buyable))
            legal_v = np.concatenate((legal_v, np.zeros(5*(7-len(self.shop)))))

        # SELL 5
        availsell = np.ones(5)
        for idx, ts in enumerate(self.team):
            if ts.pet.name=='pet-none':
                availsell[idx] = 0
        legal_v = np.concatenate((legal_v, availsell))

        # BUY FOOD (target/team) 2*5+2=12
        n_foods = 0
        for idx, slot in enumerate(self.shop):
            if slot.slot_type=='pet' or slot.slot_type=='levelup':
                continue
            if slot.item.name=='food-none':
                legal_v = np.concatenate((legal_v, np.zeros(6)))
                n_foods+=1
                continue
            if slot.slot_type=='food':
                if slot.cost>self.gold:
                    legal_v = np.concatenate((legal_v, np.zeros(6)))
                    n_foods+=1
                    continue
                # check if targeted food
                food = slot.item
                n_foods+=1
                targeted = targeted_food(food)
                if targeted:
                    # Check team slots
                    feedable = np.zeros(5)
                    for i, ts in enumerate(self.team):
                        if not ts.pet.name=='pet-none':
                            feedable[i] = 1
                    legal_v = np.concatenate((legal_v, feedable,[0]))
                else:
                    legal_v = np.concatenate((legal_v, np.zeros(5),[1]))
        # pad if less than 2 foodslots in shop
        legal_v = np.concatenate((legal_v, np.zeros((2-n_foods)*6)))

        # FREEZE/UNFREEZE 7*2=14
        canfreeze = np.zeros(14)
        for idx, slot in enumerate(self.shop):
            if slot.item.name=='pet-none' or slot.item.name=='food-none':
                continue
            if slot.frozen:
                canfreeze[7+idx] = 1
            else:
                canfreeze[idx] = 1

        legal_v = np.concatenate((legal_v, canfreeze))

        # ROLL 1
        legal_v = np.concatenate((legal_v, [1*(self.gold>0)]))
        # END TURN 1
        legal_v = np.concatenate((legal_v, [1]))
        
        if len(legal_v) != self.action_length:
            raise Exception(f"Wrong action vector size, {len(legal_v)}, not {self.action_length}")
        return legal_v

    def action_ID(self, action_idx):
        pass

    def execute(self, action_idx):
        ### Interpret action_idx and execute
        # This move should always be legal, check anyway
        if self.legal_actions[action_idx] == 0:
            raise Exception(f"Attempted Illegal Move {action_idx}")

        # MOVE 5*4=20
        if 0<=action_idx<20:
            idx = action_idx
            target = int(idx/4)
            # Other team positions
            friends = [i for i in range(5) if i!=target]
            destination = friends[idx%4] 
            self.move_to_slot(target, destination)

        # MOVE-LEVELUP 5*4=20
        elif 20<=action_idx<40:
            idx = action_idx-20
            sacrifice = int(idx/4)
            friends = [i for i in range(5) if i!=sacrifice]
            target = friends[idx%4] # pet to levelup
            self.combine(target, sacrifice)

        # BUYPET-PLACE 7*5=35
        elif 40<=action_idx<75:
            idx = action_idx-40
            s_pet = int(idx/5)
            teamspot = idx%5
            self.buy_to_spot(s_pet, teamspot)

        # BUYPET-LEVELUP 7*5=35
        elif 75<=action_idx<110:
            idx = action_idx-75
            s_pet = int(idx/5)
            teamspot = idx%5
            self.buy_combine(s_pet, teamspot)

        # SELL 5
        elif 110<=action_idx<115:
            idx = action_idx-110
            self.sell(idx)

        # BUY FOOD (target/team) 2*5+2=12
        elif 115<=action_idx<127:
            idx = action_idx-115
            food = int(idx/6)
            target = idx%6
            if target==5:
                target=None
            self.buy_food(food+5, target)

        # FREEZE/UNFREEZE 7*2=14
        elif 127<=action_idx<141:
            idx = action_idx-127
            freeze = int(idx/7)
            item = idx%7
            if freeze==0:
                self.freeze(item)
            elif freeze==1:
                self.unfreeze(item)
        
        # ROLL 1
        elif action_idx==141:
            self.roll()
        # END TURN 1
        elif action_idx==142:
            self.end_turn()

    
    @storeaction
    def start_turn(self, result=0):
        ### Update turn count and gold
        self.turn += 1
        self.gold = self.default_gold
        # bool used for snail
        if result==-1:
            self.lf_winner=False
        else:
            self.lf_winner=True
        # Calculate lives
        if result==-1:
            self.lives -= np.clip(min(3, self.turn),0)
            # Handle death in gamephase
        elif result==1:
            self.wins+=1
            # Handle victory in gamephase
        ### For terminal states, player will continue but Memory Building should not use next states            

        ### Update Shop Rules and roll shop
        self.shop.next_turn() 

        ### Activate start-of-turn triggers after rolling shop
        for slot in self.team:
            slot._pet.sot_trigger()
            
        return ()
    
    
    @storeaction
    def buy_pet(self, pet):
        """ Buy one pet from the shop """
        if len(self.team) == self._max_team:
            raise Exception("Attempted to buy Pet on full team")
        
        if type(pet) == int:
            pet = self.shop[pet]
        
        if type(pet).__name__ == "ShopSlot":
            pet = pet.item
        
        if type(pet).__name__ != "Pet":
            raise Exception("Attempted to buy_pet using object {}".format(pet))
        
        shop_idx = self.shop.index(pet)
        shop_slot = self.shop.shop_slots[shop_idx]
        cost = shop_slot.cost
        
        if cost > self.gold:
            raise Exception("Attempted to buy Pet of cost {} with only {} gold"
                            .format(cost, self.gold))
        
        ### Connect pet with current Player 
        pet.team = self.team
        pet.player = self
        pet.shop = self.shop

        ### Make all updates 
        self.gold -= cost
        self.team.append(pet)
        self.shop.buy(pet)
        
        ### Check buy_friend triggers after purchase
        for slot in self.team:
            slot._pet.buy_friend_trigger(pet)
            
        ### Check summon triggers after purchse
        for slot in self.team:
            slot._pet.friend_summoned_trigger(pet)
        
        return (pet,)
    
    
    @storeaction
    def buy_food(self, food, team_pet=None):
        """ 
        Buy and feed one food from the shop
        
        team_pet is either the purchase target or empty for food effect target

        """
        if type(food) == int:
            food = self.shop[food]
            if food.slot_type != "food":
                raise Exception("Shop slot not food")            
        if type(food).__name__ == "ShopSlot":
            food = food.item            
        if type(food).__name__ != "Food":
            raise Exception("Attempted to buy_food using object {}".format(food))
        
        if team_pet is None:
            targets, _ = get_target(food, [0, None], [self.team])
        else:
            if type(team_pet) == int:
                team_pet = self.team[team_pet]            
            if type(team_pet).__name__ == "TeamSlot":
                team_pet = team_pet._pet                
            if not self.team.check_friend(team_pet):
                raise Exception("Attempted to buy food for Pet not on team {}"
                                .format(team_pet))            
            if type(team_pet).__name__ != "Pet":
                raise Exception("Attempted to buy_pet using object {}".format(team_pet))
            targets = [team_pet]
        
        shop_idx = self.shop.index(food)
        shop_slot = self.shop.shop_slots[shop_idx]
        cost = shop_slot.cost
        
        if cost > self.gold:
            raise Exception("Attempted to buy Pet of cost {} with only {} gold"
                            .format(cost, self.gold))
            
        ### Before feeding, check for cat
        for slot in self.team:
            if slot._pet.name != "pet-cat":
                continue
            slot._pet.cat_trigger(food)
        
        ### Make all updates 
        self.gold -= cost
        self.shop.buy(food)
        for pet in targets:
            levelup = pet.eat(food)
            ### Check for levelup triggers if appropriate
            if levelup:
                pet.levelup_trigger(pet)
                self.shop.levelup()

            ### After feeding, check for eats_shop_food triggers
            for slot in self.team:
                slot._pet.eats_shop_food_trigger(pet)

        ### After feeding, check for buy_food triggers
        for slot in self.team:
            slot._pet.buy_food_trigger()
            
        ### Check if any animals fainted because of pill and if any other
        ### animals fainted because of those animals fainting
        pp = Battle.update_pet_priority(self.team, Team()) # no enemy team in shop
        status_list = []
        while True:
            ### Get a list of fainted pets
            fainted_list = []
            for _,pet_idx in pp:
                p = self.team[pet_idx].pet
                if p.name == "pet-none":
                    continue
                if p.health <= 0:
                    fainted_list.append(pet_idx)
                    if p.status != "none":
                        status_list.append([p,pet_idx])

            ### check every fainted pet
            faint_targets_list = []
            for pet_idx in fainted_list:
                fainted_pet = self.team[pet_idx].pet
                ### check for all pets that trigger off this fainted pet (including self)
                for _,te_pet_idx in pp:
                    other_pet = self.team[te_pet_idx].pet
                    te_idx = [0,pet_idx]
                    activated,targets,possible = other_pet.faint_trigger(fainted_pet,te_idx)
                    if activated:
                        faint_targets_list.append([fainted_pet,pet_idx,activated,targets,possible])

                ### If no trigger was activated, then the pet was never removed.
                ###   Check to see if it should be removed now. 
                if self.team.check_friend(fainted_pet):
                    self.team.remove(fainted_pet)

            ### If pet was summoned, then need to check for summon triggers
            for fainted_pet,pet_idx,activated,targets,possible in faint_targets_list:                
                self.check_summon_triggers(fainted_pet,pet_idx,activated,targets,possible)

            ### if pet was hurt, then need to check for hurt triggers
            hurt_list = []
            for _,pet_idx in pp:
                p = self.team[pet_idx].pet
                while p._hurt > 0:
                    hurt_list.append(pet_idx)
                    activated,targets,possible = p.hurt_trigger(Team())

            pp = Battle.update_pet_priority(self.team, Team())

            ### if nothing happend, stop the loop
            if len(fainted_list) == 0 and len(hurt_list) == 0:
                break

        ### Check for status triggers on pet
        for p,pet_idx in status_list:
            self.check_status_triggers(p,pet_idx)

        return (food,targets)


    def check_summon_triggers(self,fainted_pet,pet_idx,activated,targets,possible):
        if activated == False:
            return                
        func = get_effect_function(fainted_pet)
        if func not in [RespawnPet,SummonPet,SummonRandomPet]:
            return                        
        for temp_te in targets:
            for temp_slot in self.team:
                temp_pet = temp_slot.pet
                temp_pet.friend_summoned_trigger(temp_te)

    
    def check_status_triggers(self,fainted_pet,pet_idx):
        if fainted_pet.status not in ["status-honey-bee", "status-extra-life"]:
            return 
        
        ability = data["statuses"][fainted_pet.status]["ability"]
        fainted_pet.set_ability(ability)
        te_idx = [0,pet_idx]
        activated,targets,possible = fainted_pet.faint_trigger(fainted_pet, te_idx)
        self.check_summon_triggers(fainted_pet,pet_idx,activated,targets,possible)
    
    
    @storeaction
    def sell(self, pet):
        """ Sell one pet on the team """
        if type(pet) == int:
            pet = self.team[pet]
            
        if type(pet).__name__ == "TeamSlot":
            pet = pet._pet
            
        if type(pet).__name__ != "Pet":
            raise Exception("Attempted to sell Object {}".format(pet))
        
        ### Activate sell trigger first
        for slot in self.team:
            slot._pet.sell_trigger(pet)
            
        if self.team.check_friend(pet):
            self.team.remove(pet)

        ### Add default gold
        self.gold += 1
        
        return (pet,)
    
    
    @storeaction
    def sell_buy(self, team_pet, shop_pet):
        """ Sell one team pet and replace it with one shop pet """
        if type(shop_pet) == int:
            shop_pet = self.shop[shop_pet]
        if type(team_pet) == int:
            team_pet = self.team[team_pet]
            
        if type(shop_pet).__name__ == "ShopSlot":
            shop_pet = shop_pet.item
        if type(team_pet).__name__ == "TeamSlot":
            team_pet = team_pet._pet
        
        if type(shop_pet).__name__ != "Pet":
            raise Exception("Attempted sell_buy with Shop item {}"
                            .format(shop_pet))
        if type(team_pet).__name__ != "Pet":
            raise Exception("Attempted sell_buy with Team Pet {}"
                            .format(team_pet))
            
        ### Activate sell trigger first
        self.sell(team_pet)
        
        ### Then attempt to buy shop pet
        self.buy_pet(shop_pet)
        
        return(team_pet,shop_pet)
    
    
    def freeze(self, obj):
        """ Freeze one pet or food in the shop """
        if type(obj).__name__ == "ShopSlot":
            obj = obj.item
            shop_idx = self.shop.index(obj)
        elif type(obj) == int:
            shop_idx = obj
        shop_slot = self.shop.shop_slots[shop_idx]
        shop_slot.freeze()
        return (shop_slot,)
    
    
    def unfreeze(self, obj):
        """ Unfreeze one pet or food in the shop """
        if type(obj).__name__ == "ShopSlot":
            obj = obj.item
            shop_idx = self.shop.index(obj)
        elif type(obj) == int:
            shop_idx = obj
        shop_slot = self.shop.shop_slots[shop_idx]
        shop_slot.unfreeze()
        return (shop_slot,)
    
    #Move from start id to target id
    def move_to_slot(self, sidx, tidx):
        target = self.team[tidx]
        start = self.team[sidx]
        if start.empty:
            raise Exception("Attempted to move a slot that is empty")

        if target.empty:
            self.team[tidx] = start
            self.team[sidx] = TeamSlot(seed_state = self.team.seed_state)

        if not target.empty:
            half1 = []
            half2 = []
            newteampet = []
            
            tempteam = self.team
            tempteam[sidx] = TeamSlot(seed_state = self.team.seed_state)

            newteampet.append(start)
            newL = 0
            for petid in range(self._max_team):
                if petid < tidx:
                    half1.append(tempteam[petid])
                if petid >= tidx:
                    half2.append(tempteam[petid])
            
            new_team = []
            if tidx == 0:
                new_team += [x for x in newteampet]
                new_team += [x for x in half1]
                new_team += [x for x in half2]

            if tidx == self._max_team:
                new_team += [x for x in half1]
                new_team += [x for x in half2]
                new_team += [x for x in newteampet]
            
            if tidx != 0 and tidx != self._max_team:
                new_team += [x for x in half1]
                new_team += [x for x in newteampet]
                new_team += [x for x in half2]

            for pet in new_team:
                newL += 1

            if newL == self._max_team:
                self.team = Team([new_team[x] for x in range(0,self._max_team)],
                            seed_state=self.team.seed_state)

            if newL > self._max_team:
                emptydel = False
                if not new_team[0].empty and not new_team[self._max_team].empty:
                    if tidx < (self._max_team/2):
                        for petx in new_team:
                            if petx.empty and (emptydel == False):
                                del(new_team[new_team.index(petx)])
                                emptydel = True
                    if tidx > (self._max_team/2):
                        for petx in reversed(new_team):
                            if petx.empty and (emptydel == False):
                                del(new_team[new_team.index(petx)])
                                emptydel = True

                if new_team[0].empty and not new_team[self._max_team].empty:
                    del(new_team[0])
                
                self.team = Team([new_team[x] for x in range(0,self._max_team)],
                            seed_state=self.team.seed_state)

    @storeaction
    def roll(self):
        """ Roll shop """
        if self.gold < 1:
            raise Exception("Attempt to roll without gold")
        self.shop.roll()
        self.gold -= 1
        return ()

    @staticmethod
    def combine_pet_stats(pet_to_keep, pet_to_be_merged):
        """ Pet 1 is the pet that is kept"""
        c_attack = max(pet_to_keep._attack, pet_to_be_merged._attack) + 1
        c_until_end_of_battle_attack = max(pet_to_keep._until_end_of_battle_attack_buff,
                                           pet_to_be_merged._until_end_of_battle_attack_buff)
        c_health = max(pet_to_keep._health, pet_to_be_merged._health) + 1
        c_until_end_of_battle_health = max(pet_to_keep._until_end_of_battle_health_buff,
                                           pet_to_be_merged._until_end_of_battle_health_buff)
        cstatus = get_combined_status(pet_to_keep, pet_to_be_merged)

        pet_to_keep._attack = c_attack
        pet_to_keep._health = c_health
        pet_to_keep._until_end_of_battle_attack_buff = c_until_end_of_battle_attack
        pet_to_keep._until_end_of_battle_health_buff = c_until_end_of_battle_health
        pet_to_keep.status = cstatus
        levelup = pet_to_keep.gain_experience()

        # Check for levelup triggers if appropriate
        if levelup:
            # Activate the ability of the previous level
            pet_to_keep.level -= 1
            pet_to_keep.levelup_trigger(pet_to_keep)
            pet_to_keep.level += 1
        
        return levelup
    
    @storeaction
    def buy_combine(self, shop_pet, team_pet):
        """ Combine two pets on purchase """
        if type(shop_pet) == int:
            shop_pet = self.shop[shop_pet]
        if type(team_pet) == int:
            team_pet = self.team[team_pet]
            
        if type(shop_pet).__name__ == "ShopSlot":
            shop_pet = shop_pet.item
        if type(team_pet).__name__ == "TeamSlot":
            team_pet = team_pet._pet
        
        if type(shop_pet).__name__ != "Pet":
            raise Exception("Attempted buy_combined with Shop item {}"
                            .format(shop_pet))
        if type(team_pet).__name__ != "Pet":
            raise Exception("Attempted buy_combined with Team Pet {}"
                            .format(team_pet))
        if team_pet.name != shop_pet.name:
            raise Exception("Attempted combine for pets {} and {}"
                            .format(team_pet.name, shop_pet.name))
        
        shop_idx = self.shop.index(shop_pet)
        shop_slot = self.shop.shop_slots[shop_idx]
        cost = shop_slot.cost
        
        if cost > self.gold:
            raise Exception("Attempted to buy Pet of cost {} with only {} gold"
                            .format(cost, self.gold))
        
        ### Make all updates 
        self.gold -= cost
        self.shop.buy(shop_pet)
        
        levelup = Player.combine_pet_stats(team_pet, shop_pet)
        if levelup:
            self.shop.levelup()
            
        ### Check for buy_pet triggers
        for slot in self.team:
            slot._pet.buy_friend_trigger(team_pet)
            
        return shop_pet,team_pet

    @storeaction
    def buy_to_spot(self, pet, tidx):
        
        """ Place pet to team slot on purchase """
        if len(self.team) == self._max_team:
            raise Exception("Attempted to buy Pet on full team")

        if type(pet) == int:
            pet = self.shop[pet]
            
        if type(pet).__name__ == "ShopSlot":
            pet = pet.item
        
        if type(pet).__name__ != "Pet":
            raise Exception("Attempted buy_combined with Shop item {}"
                            .format(pet))
        if type(tidx) != int:
            raise Exception("Attempted buy_to_spot with target idx {}")
        
        shop_idx = self.shop.index(pet)
        shop_slot = self.shop.shop_slots[shop_idx]
        cost = shop_slot.cost
        
        if cost > self.gold:
            raise Exception("Attempted to buy Pet of cost {} with only {} gold"
                            .format(cost, self.gold))
        
        ### Connect pet with current Player 
        pet.team = self.team
        pet.player = self
        pet.shop = self.shop

        ### Make all updates 
        self.gold -= cost
        self.shop.buy(pet)

        target = self.team[tidx]
        newteampet = TeamSlot(obj=pet,seed_state=self.team.seed_state)
        if not target.empty:
            half1 = []
            half2 = []
            newteampetL = []
            newteampetL.append(newteampet)

            tempteam = self.team
            newL = 0
            for petid in range(self._max_team):
                if petid < tidx:
                    half1.append(tempteam[petid])
                if petid >= tidx:
                    half2.append(tempteam[petid])

            new_team = []
            if tidx == 0:
                new_team += [x for x in newteampetL]
                new_team += [x for x in half1]
                new_team += [x for x in half2]

            if tidx == (self._max_team-1):
                new_team += [x for x in half1]
                new_team += [x for x in half2]
                new_team += [x for x in newteampetL]
            
            if tidx != 0 and tidx != (self._max_team-1):
                new_team += [x for x in half1]
                new_team += [x for x in newteampetL]
                new_team += [x for x in half2]

            for x in new_team:
                newL += 1

            if newL == self._max_team:
                self.team = Team([new_team[x] for x in range(0,self._max_team)],
                            seed_state=self.team.seed_state)

            if newL > self._max_team:
                emptydel = False
                if not new_team[0].empty and not new_team[self._max_team].empty:
                    if tidx < (self._max_team/2):
                        for petx in new_team:
                            if petx.empty and (emptydel == False):
                                del(new_team[new_team.index(petx)])
                                emptydel = True
                    if tidx > (self._max_team/2):
                        for petx in reversed(new_team):
                            if petx.empty and (emptydel == False):
                                del(new_team[new_team.index(petx)])
                                emptydel = True

                if new_team[0].empty and not new_team[self._max_team].empty:
                    del(new_team[0])
                
                self.team = Team([new_team[x] for x in range(0,self._max_team)],
                            seed_state=self.team.seed_state)

        if target.empty:
            self.team[tidx] = newteampet
            
        ### Check for buy_pet triggers
        for slot in self.team:
            slot._pet.buy_friend_trigger(pet)
        
        ### Check summon triggers after purchse
        for slot in self.team:
            slot._pet.friend_summoned_trigger(pet)
        
        return (pet,)

    @storeaction
    def combine(self, pet1, pet2):
        """ Combine two pets on the team together """
        if type(pet1) == int:
            pet1 = self.team[pet1]
        if type(pet2) == int:
            pet2 = self.team[pet2]
            
        if type(pet1).__name__ == "TeamSlot":
            pet1 = pet1._pet
        if type(pet2).__name__ == "TeamSlot":
            pet2 = pet2._pet
        
        if not self.team.check_friend(pet1):
            raise Exception("Attempted combine for Pet not on team {}"
                            .format(pet1))
        if not self.team.check_friend(pet2):
            raise Exception("Attempted combine for Pet not on team {}"
                            .format(pet2))
        
        if pet1.name != pet2.name:
            raise Exception("Attempted combine for pets {} and {}"
                            .format(pet1.name, pet2.name))

        levelup = Player.combine_pet_stats(pet1, pet2)
        if levelup:
            self.shop.levelup()
        
        ### Remove pet2 from team
        idx = self.team.index(pet2)
        self.team[idx] = TeamSlot()
        
        return pet1,pet2 
        
    
    @storeaction
    def reorder(self, idx):
        """ Reorder team """
        if len(idx) != len(self.team):
            raise Exception("Reorder idx must match team length")
        unique = np.unique(idx)
        
        if len(unique) != len(self.team):
            raise Exception("Cannot input duplicate indices to reorder: {}"
                            .format(idx))
            
        self.team = Team([self.team[x] for x in idx],
                         seed_state=self.team.seed_state)
        
        return idx
    
    
    @storeaction
    def end_turn(self):
        """ End turn and move to battle phase """
        ### Activate eot trigger
        for slot in self.team:
            slot._pet.eot_trigger()
        return None
        
        
    @property
    def state(self):
        state_dict = {
            "type": "Player",
            "team": self.team.state,
            "shop": self.shop.state,
            "lives": self.lives, 
            "default_gold": self.default_gold, 
            "gold": self.gold, 
            "lf_winner": self.lf_winner,
            "pack": self.pack,
            "turn": self.turn, 
            "action_history": self.action_history,
            "wins": self.wins,
        }
        return state_dict
    
    
    @classmethod
    def from_state(cls, state):
        team = Team.from_state(state["team"])
        shop_type = state["shop"]["type"]
        shop_cls = getattr(sapai.shop, shop_type)
        shop = shop_cls.from_state(state["shop"])
        if "action_history" in state:
            action_history = state["action_history"]
        else:
            action_history=[]
        return cls(team=team,
                   shop=shop,
                   lives=state["lives"],
                   default_gold=state["default_gold"],
                   gold=state["gold"],
                   turn=state["turn"],
                   lf_winner=state["lf_winner"],
                   pack=state["pack"],
                   action_history=action_history,
                   wins=state["wins"])
    
    
    def __repr__(self):
        info_str =  "PACK:  {}\n".format(self.pack)
        info_str += "TURN:  {}\n".format(self.turn)
        info_str += "LIVES: {}\n".format(self.lives)
        info_str += "WINS:  {}\n".format(self.wins)
        info_str += "GOLD:  {}\n".format(self.gold)
        print_str = "--------------\n"
        print_str += "CURRENT INFO: \n--------------\n"+info_str+"\n"
        print_str += "CURRENT TEAM: \n--------------\n"+self.team.__repr__()+"\n"
        print_str += "CURRENT SHOP: \n--------------\n"+self.shop.__repr__()
        return print_str
    
    
def get_combined_status(pet1, pet2):
    """
    Statuses are combined based on the tier that they come from.
    
    """
    status_tier = {
        0: ["status-weak", "status-poison-attack", "none"],
        1: ["status-honey-bee"],
        2: ["status-bone-attack"],
        3: ["status-garlic-armor"],
        4: ["status-splash-attack"],
        5: ["status-coconut-shield", "status-melon-armor", "status-steak-attack", "status-extra-life"],
    }
    
    status_lookup = {}
    for key,value in status_tier.items():
        for entry in value:
            status_lookup[entry] = key
    
    ### If there is a tie in tier, then pet1 status is used
    max_idx = np.argmax([status_lookup[pet1.status], 
                         status_lookup[pet2.status]])
    
    return [pet1.status, pet2.status][max_idx]