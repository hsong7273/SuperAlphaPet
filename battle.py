#         1. execute start-of-turn abilities according to pet priority
#         2. perform hurt and faint abilities according to pet priority
#                 2.1 Execute 2 until there are no new fainted animals
#         3. before-attack abilities according to pet priority
#         4. perform fainted pet abilities via pet priority
#                 4.1 Execute 4 until there are no new fainted animals
#         5. attack phase 
#             5.0 perform before_attack abilities
#             5.1. perform hurt and fainted abilities according to pet priority
#                    5.1.1 Execute 5.1 until there are no new fainted animals
#             5.2 perform attack damage
#             5.3 perform after attack abilities
#             5.4 perform hurt and fainted abilities according to pet priority
#                    5.4.1 Execute 5.4 until there are no new fainted animals
#             5.5. check if knock-out abilities should be performed
#                     5.5.1 if knock-out ability activated jump to 5.5
#             5.6. if battle has not ended, jump to 5.0

import numpy as np

class Battle:

    #Param: team1,team2 = arrays of pet objects
    def __init__(self, team1, team2):
        self.team1 = team1
        self.team2 = team2

    #Param types: team1,array team2,array
    def getStartEffectsTemp(team1, team2):
        #get attack numbers of both teams and sort

        for x in team1:
            if x.trigger == "On Start":
                #doeffect
                x.needs #list of info that x needs (team1, team2, shop, gold)
                x.effect() #battle needs to grab everything that x needs to do effect (* operator is arbitrary args)
                return
    #----------------------------------------------------------------------------
    #Param types: team1,array team2,array
    #List of battle start effects:
    #1. Deal dmg to random/defined(based on positioning/triggers/stats) enemies
    #3. Give attack and/or hp to random friends
    #4. Gain attack and/or hp based on friends with certain triggers
    #5. Give attack and/or hp to friends with certain positioning
    #11. Reduce hp of target
    #12. Swallow friend ahead then release it as level 1/2/3 after fainting (whale)


    #DLC start effects:
    #2. Swap stats of the 2 adjacent friends (dlc)
    #6. Make enemies weak (take +n extra dmg) (dlc)
    #7. Give friend xp (dlc)
    #8. Give attack and/or hp then faint (dlc)
    #9. Copy lvl 1/2/3 ability from highest tier enemy (dlc)
    #10. Evolve??? (caterpillar dlc)
    #13. If highest tier pet, gain attack and hp (lion dlc)
    #14. Deal damage to target and self (dlc)
    #15. Swap stats, shuffle positioning, both (hyena dlc)
    #16. Give shield to friends (velociraptor dlc)
    #17. Make friends level 3 (white tiger dlc)

    def getStartEffects(team1, team2):
        tempTeam1 = []
        tempTeam2 = []

        #create arrays of pet dictionaries for respective teams
        petInd = 0
        for pet in team1:
            petDict = dict({
                'name': pet.name,
                'team': 1,
                'attack': pet.attack,
                'maxhealth': pet.health,
                'index': petInd
            })
            tempTeam1.append(petDict)
            petInd += 1
        
        petInd = 0
        for pet in team2:
            petDict = dict({
                'name': pet.name,
                'team': 2,
                'attack': pet.attack,
                'maxhealth': pet.health,
                'index': petInd
            })
            tempTeam2.append(petDict)
            petInd += 1

        #sort both teams together high attack --> low(bubblesort)
        sortedTeams = np.concatenate(tempTeam1,tempTeam2)
        n = len(sortedTeams)
        for x in range(n):
            for y in range(0, n-x-1):
                if sortedTeams[y]['attack'] < sortedTeams[y+1]['attack']:
                    sortedTeams[y],sortedTeams[y+1] = sortedTeams[y+1],sortedTeams[y]
                
        #for dupe attack, check hp values
        for x in range(n):
            if sortedTeams[x]['attack'] == sortedTeams[x+1]['attack']:
                if sortedTeams[x]['maxhealth'] < sortedTeams[x]['maxhealth']:
                    sortedTeams[x],sortedTeams[x+1] = sortedTeams[x+1],sortedTeams[x]
                elif sortedTeams[x]['maxhealth'] == sortedTeams[x]['maxhealth']:
                    rng = np.random.randint(2)
                    if rng == 0:
                        pass
                    if rng == 1:
                        sortedTeams[x],sortedTeams[x+1] = sortedTeams[x+1],sortedTeams[x]

        #triggers effects in sorted order
        #types: sortedTeams (array of dictionaries) pet (dictionary) team1,team2 (array of pet objects)
        for pet in sortedTeams:
            
            if pet['team'] == 1:
                if team1[pet['index']].trigger == "On Start":
                    #do effect to self or team2
                    pass

            if pet['team'] == 2:
                if team2[pet['index']].trigger == "On Start":
                    #do effect to self or team1 
                    pass
            
    #----------------------------------------------------------------------------
    #Param types: team,array
    def checkBattleTeamCount(team):
        #checks active pet count in team
        count = 0
        for x in team:
            if x.status == "active":
                count += 1
        return count

    #----------------------------------------------------------------------------
    #Param types: team1,array team2,array
    def doAttack(team1, team2):
        team1.getFront().takedamage(team1.getFront(),team2.getFront().attack)
        team2.getFront().takedamage(team2.getFront(),team1.getFront().attack)

    #----------------------------------------------------------------------------
    #effects for battle: Faint, friend summoned, before attack?, hurt, friend attacks, friend faints, knockout, friend repeats ability 
    def getEffects():
        
        return

    #---------------------------------------------------------------------------- 

#Param: battle class
def doBattle(battle):
    #check start effects--
    #apply start effects
    #while either team count > 0
        #do attack
        #check pet hp
        #check effect?
    #if either team == 0, declare winner

#         1. execute start-of-turn abilities according to pet priority
#         2. perform hurt and faint abilities according to pet priority
#                 2.1 Execute 2 until there are no new fainted animals
#         3. before-attack abilities according to pet priority
#         4. perform fainted pet abilities via pet priority
#                 4.1 Execute 4 until there are no new fainted animals
#         5. attack phase 
#             5.0 perform before_attack abilities
#             5.1. perform hurt and fainted abilities according to pet priority
#                    5.1.1 Execute 5.1 until there are no new fainted animals
#             5.2 perform attack damage
#             5.3 perform after attack abilities
#             5.4 perform hurt and fainted abilities according to pet priority
#                    5.4.1 Execute 5.4 until there are no new fainted animals
#             5.5. check if knock-out abilities should be performed
#                     5.5.1 if knock-out ability activated jump to 5.5
#             5.6. if battle has not ended, jump to 5.0


    teamcount1 = battle.checkBattleTeamCount(battle.team1)
    

    return


class Team:
    def __init__(self, pet1, pet2, pet3, pet4, pet5):
        self.pets = [pet1, pet2, pet3, pet4, pet5]
    
    #----------------------------------------------------------------------------
    #Param types: team,array of pets
    def getFront(team):
        #gets pet in front of line. if no pets active, return null/None
        for x in team:
            if x.status == "active":
                return x
        return None
