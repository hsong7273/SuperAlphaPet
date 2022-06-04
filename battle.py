#

class Battle:
    def doBattle():
        #check start effects
        #apply start effects
        #while either team count > 0
            #do attack
            #check pet hp
            #check effect?
        #if either team == 0, declare winner

        return

    def __init__(self, team1, team2):
        self.team1 = team1
        self.team2 = team2

    def getStartEffects(team1, team2):
        #get attack numbers of both teams and sort

        for x in team1:
            if x.trigger == "On Start":
                #doeffect
                x.needs #list of info that x needs (team1, team2, shop, gold)
                x.effect() #battle needs to grab everything that x needs to do effect (* operator is arbitrary args)
                return
    
    def setFront():
        #sets pet to front of line
        return

    def doAttack():
        #front line pets attack each other
        return
    
    def getEffects():
        #check for faint, 
        return


class Team:
    def __init__(self, pet1, pet2, pet3, pet4, pet5):
        self.pet1 = pet1
        self.pet2 = pet2
        self.pet3 = pet3
        self.pet4 = pet4
        self.pet5 = pet5