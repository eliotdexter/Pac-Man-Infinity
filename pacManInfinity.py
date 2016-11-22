import cocos
from cocos.actions import *
import time
import random
import copy

class Apple(cocos.sprite.Sprite):
    def __init__(self,cx,cy,bx,by):
        image = "fruitSprite.png"
        super(Apple,self).__init__(image)
        self.position = (cx,cy) #Pixel position
        self.location = (bx,by) #position on board, only used when sleeping

class Dot(cocos.sprite.Sprite):
    def __init__(self,pellet,cx,cy,bx,by):
        image = "dotSprite.png"
        self.pellet = pellet
        if(pellet == True): image = "pelletSprite.png"
        super(Dot,self).__init__(image)
        self.position = (cx,cy) #Pixel position
        self.location = (bx,by) #position on board, only used when sleeping

    def __repr__(self):
        return "Dot: " + str(self.location)

class Ghost(cocos.sprite.Sprite):
    def __init__(self,image,cx,cy,bx,by):
        super(Ghost,self).__init__(image)
        self.position = (cx,cy) #Pixel position
        self.location = (bx,by) #position on board, only used when sleeping
        self.asleep = True #Ghost starts asleep
        self.alertDelay = 0
        self.inTrain = False #Starts outside train
        self.color = ("67","227","61")
        self.originalColor = ("67","227","61")

    def update(self,board,pelletActive):
        if(self.inTrain == True or pelletActive == True):
            return #Ghosts are managed by train later
        elif(self.checkIfPacManNearby(board) == True):
            self.asleep = False #Wake ghost
            self.alertDelay = 5
            self.color = ("242","41","41")
            self.originalColor = ("242","41","41")
        elif(self.alertDelay > 0):
            self.alertDelay -= 1 #Ghost waits for train
        elif(self.alertDelay == 0):
            self.asleep == True
            self.color = ("67","227","61")
            self.originalColor = ("67","227","61")

    def move(self,bdx,bdy,board,cellSize):
        previousLoc = self.location
        newX,newY = (self.location[0]+bdx,self.location[1]+bdy)
        
        #Going into a solid block
        if(board[newY][newX] == "s"): 
            #Do nothing if block is solid
            return

        oldPX, oldPY = self.position
        self.position = (oldPX+bdx*cellSize,oldPY+bdy*-cellSize)
        self.location = (newX,newY)

    def __eq__(self,other):
        try: #Type here is on purpose, must be a ghost, not another sprite!!
            return (self.location == other.location) and (type(other) == Ghost)
        except: return False

    def __hash__(self):
        return hash(self.location)

    #repr mainly here for debugging
    def __repr__(self):
        return "Ghost at location: " + str(self.location)

    #Use for collisions with pacMan, only focusing on the center point
    def pointIntersects(self,px,py):
        if self.cointains(x,y): return True
        else: return False

    def checkIfPacManNearby(self,pacManLoc):
        adjacentDirs = [(1,0),(-1,0),(0,1),(0,-1)]

        for direction in adjacentDirs:
            bx,by = self.location
            dx,dy = direction
            newX = bx + dx
            newY = by + dy

            #If he's adjacent, return True
            if((newX,newY) == pacManLoc): return True

        return False

class GhostSnake(object):
    def __init__(self,bx,by):
        self.bx = bx
        self.by = by
        self.ghostTrain = []

        self.lbx = None
        self.lby = None
        self.route = [] #Series of moves snake will make
        self.delay = 0 #Wait if told to 

    def addAdjacentGhosts(self,ghostList):
        ghostsToRemove = []
        minDistance = 1.1 #Compensate for floating point error
        for ghost in ghostList:
            ghostBX,ghostBY = ghost.location
            distance = ((ghostBX-self.bx)**2 + (ghostBY-self.by)**2)**0.5

            if(distance <= minDistance and ghost.asleep == False):
                ghostsToRemove.append(ghost)
                ghost.color = ("242","41","219")
                ghost.originalColor = ("242","41","219")

        self.ghostTrain += ghostsToRemove

        ghostList=[ghost for ghost in ghostList if ghost not in ghostsToRemove]

        return ghostList

    def move(self,board,pacManLoc):

        if(pacManLoc not in self.route):
            self.route += [pacManLoc]

        pacX,pacY = pacManLoc
        distance = ((pacX-self.bx)**2 + (pacY-self.by)**2)**0.5
        if(distance <= 3 and random.randint(1,3) == 2): return
        #If snake is close, occasionally skip moves to let pac-man live

        if(len(self.route) > 0 and self.delay <= 0):
            self.bx,self.by = self.route[0]
            self.route.pop(0)
        else: #Means delay is not zero
            self.delay -= 1

    #Move all ghosts with the front of the snake
    def moveGhosts(self,board,cellSize):
        nextLoc = (self.bx,self.by)
        for ghost in self.ghostTrain:
            nextBx,nextBy = nextLoc
            lastBx,lastBy = ghost.location

            if(nextBy < 0): nextBy = len(board)-1
            elif(nextBy >= len(board)): nextBy = 0
            elif(nextBx < 0): nextBx = len(board[0])-1
            elif(nextBx >= len(board[0])): nextBx = 0

            ghost.move(nextBx-lastBx,nextBy-lastBy,board,cellSize)
            nextLoc = (lastBx,lastBy)
            #Moves up every ghost in the chain

#PacMan class stores all atributes
class PacMan(cocos.sprite.Sprite):
    def __init__(self,image,px,py,bx,by):
        super(PacMan,self).__init__(image)
        self.position = (px,py) #Location in terms of pixels
        self.location = (bx,by) #Location in terms of the board
        self.bdx = -1
        self.bdy = 0
        self.moveSet = set()

    #What happens to PacMan every timer fired
    def move(self,board,cellSize,dt):
        previousLoc = self.location
        self.location = (self.location[0]+self.bdx,self.location[1]+self.bdy)

        #If off board,loop back around
        if(self.location[0] < 0):
            self.location = (len(board[0])-1,self.location[1])
            self.position = (self.position[0]+(len(board[0])-1)*cellSize,self.position[1])

        elif(self.location[0] >= len(board[0])):
            self.location = (0,self.location[1])
            self.position = (self.position[0]-(len(board[0])-1)*cellSize,self.position[1])

        elif(self.location[1] < 0):
            self.location = (self.location[0],len(board)-1)
            self.position = (self.position[0],self.position[1]-(len(board)-1)*cellSize)

        elif(self.location[1] >= len(board)):
            self.location = (self.location[0],0)
            self.position = (self.position[0],self.position[1]+(len(board)-1)*cellSize)
        
        #Going into a solid block
        elif(board[self.location[1]][self.location[0]] == "s"): 
            #Undo move
            self.location = previousLoc
            return

        else: #Otherwise, make the changes on the screen
            self.position = (self.position[0]+self.bdx*cellSize,
                         self.position[1]+self.bdy*-cellSize)

        board[self.location[1]][self.location[0]] = "p"
        board[previousLoc[1]][previousLoc[0]] = "e"


class GameLayer(cocos.tiles.RectMapLayer):
    is_event_handler = True
    def __init__(self,cellSize):
        self.cellSize = cellSize
        cells,self.board = self.makeGrid(cellSize)
        self.mazeCenter = (15,9)

        super(GameLayer,self).__init__(None,cellSize,cellSize,cells)
        self.keys_pressed = set()

        self.pacManInit()

        self.ghostSnake = GhostSnake(*self.mazeCenter)

        self.directionToMove = None
        self.currentDirection = "left"

        self.add(self.pacMan)
        self.set_view(-7,20,self.px_width,self.px_height)

        self.leftDots=self.rightDots=self.leftGhosts=self.rightGhosts=[]

        self.rightDots,self.rightGhosts = self.mazeEntityPlacer('right')
        self.leftDots,self.leftGhosts = self.mazeEntityPlacer('left')
        for item in (self.leftDots+self.rightDots+
                     self.leftGhosts+self.rightGhosts):
            self.add(item)

        self.leftFruitOut = self.rightFruitOut = False
        leftBX,leftBY = 18,4
        rightBX,rightBY = 12,12
        px,py = self.cells[leftBY][leftBX].center
        self.leftFruit = Apple(px,py,leftBX,leftBY)
        px,py = self.cells[rightBY][rightBX].center
        self.rightFruit = Apple(px,py,rightBX,rightBY)

        self.score = 0
        self.livesScoreCounter = 0
        #Uses integer division to keep track of granting extra lives

        self.lives = 5 #Start with 5 lives
        self.speed = 1 #Starts at 1, goes up to 50
        self.maxSpeed = 75

        self.pelletTimer = 0
        self.pelletConstant = 40

        self.delayConstant = 20
        self.scoreStreak = 0

        self.scoreLabel = cocos.text.Label('Score:',
        font_name='Arial',font_size=16,anchor_x='center', anchor_y='center')

        self.scoreText = cocos.text.Label(str(self.score),
        font_name='Arial',font_size=16,anchor_x='center', anchor_y='center')

        self.scoreLabel.position = (545,610)
        self.scoreText.position = (545,570)
        self.add(self.scoreLabel)
        self.add(self.scoreText)

        self.speedLabel = cocos.text.Label('Speed:',
        font_name='Arial',font_size=32,anchor_x='center', anchor_y='center')

        self.speedText = cocos.text.Label(str(self.speed),
        font_name='Arial',font_size=32,anchor_x='center', anchor_y='center')

        self.speedLabel.position = (545,150)
        self.speedText.position = (545,70)
        self.add(self.speedLabel)
        self.add(self.speedText)

        self.pelletLabel = cocos.text.Label('Power-Up: %d' % self.pelletTimer,
        font_name='Arial',font_size=16,anchor_x='center', anchor_y='center')

        self.pelletLabel.position = (1000,610)
        self.add(self.pelletLabel)

        self.livesLabel = cocos.text.Label('Lives: %d' % self.lives,
        font_name='Arial',font_size=16,anchor_x='center', anchor_y='center')

        self.pauseLabel = cocos.text.Label('Game Paused',
        font_name='Arial',font_size=64,anchor_x='center', anchor_y='center')

        self.pauseLabel.position = (550,370)

        self.livesLabel.position = (100,610)
        self.add(self.livesLabel)
        self.paused = False
        self.gracePeriod = 0
        self.extraLivesCutoff = 500000

        self.initSplashScreen()

    def initSplashScreen(self):
        text = """
    Instructions:

    Use the arrow keys to move Pac-Man.
    Ghosts will follow you as you go around the maze.
    Once you consume all of the dots on one half of the maze, fruit will appear.
    If you eat the fruit, the completed half of the maze will regenerate.
    As you score more, the game speed will increase.
    The greater the speed, the higher your score!
    If you eat a power pellet, you can eat ghosts and score even more!
    You will be given an extra life every %d points you score.
    You may also press 'p' to pause at any time.

    Good Luck!

    Press Enter to begin
        """ % self.extraLivesCutoff
        self.splashScreenUp = True
        self.splashScreenText = cocos.text.Label(text,multiline=True,width=1000,
        font_name='Arial',font_size=16,anchor_x='center', anchor_y='center')
        self.splashTitle = cocos.text.Label("Welcome to Pac-Man Infinity",
        font_name='Arial',font_size=32,anchor_x='center', anchor_y='center')

        self.splashScreenText.position = (700,300)
        self.splashTitle.position = (550,500)

        self.add(self.splashScreenText)
        self.add(self.splashTitle)

    def pacManInit(self):
        startBX,startBY = 15,10
        self.board[startBY][startBX] = "p"

        px,py = self.cells[startBY][startBX].center
        self.pacMan = PacMan("pacManPlaceholder.png",px,py,startBX,startBY)

    #Messes with the scheduler
    def changeSpeed(self):
        self.speed = (self.scoreStreak//50)+1
        if(self.speed > 50): self.speed = 50

        minDelay = 0.05
        maxDelay = 0.125
        speedRange = maxDelay-minDelay
        dt = speedRange*((self.maxSpeed-self.speed)/self.maxSpeed)+minDelay
        
        time.sleep(dt)

    def checkGhostCollision(self):
        ghostsToCheck = (self.leftGhosts+self.rightGhosts+
                         self.ghostSnake.ghostTrain) 

        for ghost in ghostsToCheck:
            if(ghost.location == self.pacMan.location):
                #Pac-Man dies if he gets hit
                if(self.pelletTimer <= 0 and self.gracePeriod == 0):
                    self.lives -= 1
                    self.gracePeriod = 10
                    self.ghostSnake.bx,self.ghostSnake.by = self.mazeCenter
                    self.scoreStreak = 0 #Reset streak

                    for ghost in self.ghostSnake.ghostTrain: #Snake to center
                        defX,defY = self.mazeCenter
                        ghost.location = (defX,defY)
                        ghost.position = self.cells[defY][defX].center

                    self.ghostSnake.delay = self.delayConstant
                    self.speed = 1 #Speed reset

                elif(self.pelletTimer > 0): #Pac-Man kills ghost
                    self.pelletTimer += 5 #So you can wipe out huge chains
                    self.score += 100*self.speed
                    self.scoreStreak += 100

                    if(ghost in self.leftGhosts):
                        self.leftGhosts.remove(ghost)
                    elif(ghost in self.rightGhosts):
                        self.rightGhosts.remove(ghost)

                    elif(ghost in self.ghostSnake.ghostTrain):
                        self.ghostSnake.ghostTrain.remove(ghost)

                    #To prevent issues with overlapping ghosts
                    try:self.remove(ghost)
                    except:pass

    #Reads in user input from keyboard
    def changeDirection(self):
        upID = 65362
        downID = 65364
        leftID = 65361
        rightID = 65363
        pauseID = 112 #I love the irony here
        enterID = 65293
        if(upID in self.keys_pressed): self.directionToMove = "up"
        elif(downID in self.keys_pressed): self.directionToMove = "down"
        elif(leftID in self.keys_pressed): self.directionToMove = "left"
        elif(rightID in self.keys_pressed): self.directionToMove = "right"
        elif(pauseID in self.keys_pressed): self.doPause(pauseID)

        elif(enterID in self.keys_pressed and self.splashScreenUp == True):
            self.closeSplashScreen()

    def closeSplashScreen(self):
        self.splashScreenUp = False
        self.remove(self.splashScreenText)
        self.remove(self.splashTitle)
        #Schedule acts like an internal timer-fired
        self.schedule(self.update)

    def doPause(self,pauseID):
        if(self.paused == False):
            self.pause_scheduler()
            self.paused = True
            self.add(self.pauseLabel)

        elif(self.paused == True):
            self.resume_scheduler()
            self.paused = False
            self.remove(self.pauseLabel)

        if(pauseID in self.keys_pressed):
            self.keys_pressed.remove(pauseID)

    def reinit(self):
        self.add(self.pacMan)
        #If in a solid block now, move it back to the center
        if(self.board[self.ghostSnake.by][self.ghostSnake.bx] == 's'):
            self.ghostSnake.bx,self.ghostSnake.by = self.mazeCenter
        self.ghostSnake.moveGhosts(self.board,self.cellSize)
        #Add the ghostSnake back
        for ghost in self.ghostSnake.ghostTrain: self.add(ghost)

        if(self.leftFruitOut == True): self.add(self.leftFruit)
        if(self.rightFruitOut == True): self.add(self.rightFruit)

        self.add(self.scoreText)
        self.add(self.scoreLabel)

        self.add(self.speedLabel)
        self.add(self.speedText)

        self.add(self.pelletLabel)
        self.add(self.livesLabel)

    def checkIfLeftFruitEaten(self):
        if(self.pacMan.location == self.leftFruit.location and
            self.leftFruitOut == True):

            self.leftFruitOut = False
            self.remove(self.leftFruit)

            self.score += 50*self.speed
            self.scoreStreak += 50

            tempBoard = self.board.copy()
            tempBoard = self.leftMazeReplacer(tempBoard)
            cells = GameLayer.boardConverter(tempBoard,self.cellSize)
            self.board = tempBoard

            super(GameLayer,self).__init__(None,self.cellSize,self.cellSize,cells)
            self.set_view(-7,20,self.px_height,self.px_width+self.cellSize*13)

            #Repopulate left half of maze
            self.leftDots,self.leftGhosts = self.mazeEntityPlacer('left')
            for item in (self.leftDots+self.rightDots+
                     self.leftGhosts+self.rightGhosts): self.add(item)

            self.reinit() #Re-init all of the necessary stuff

    def checkIfRightFruitEaten(self):
        if(self.pacMan.location == self.rightFruit.location and
            self.rightFruitOut == True):

            self.rightFruitOut = False
            self.remove(self.rightFruit)

            self.score += 50*self.speed
            self.scoreStreak += 50

            tempBoard = self.board.copy()
            tempBoard = self.rightMazeReplacer(tempBoard)
            cells = GameLayer.boardConverter(tempBoard,self.cellSize)

            self.board = tempBoard

            super(GameLayer,self).__init__(None,self.cellSize,self.cellSize,cells)
            self.set_view(-7,20,self.px_height,self.px_width+self.cellSize*13)

            #Repopulate right half of maze
            self.rightDots,self.rightGhosts = self.mazeEntityPlacer('right')
            
            for item in (self.leftDots+self.rightDots+
                     self.leftGhosts+self.rightGhosts):
                self.add(item)

            self.reinit() #Re-init all of the necessary stuff

    def checkForLeftClear(self):
        if(len(self.leftDots) == 0 and self.leftFruitOut == False):
            self.leftFruitOut = True
            self.add(self.leftFruit)

    def checkForRightClear(self):
        if(len(self.rightDots) == 0 and self.rightFruitOut == False):
            self.rightFruitOut = True
            self.add(self.rightFruit)

    #Makes every ghost blue
    def setGhostColorBlue(self):
        blueRGBTuple = ("41","118","242")
        ghostsToCheck = (self.leftGhosts+self.rightGhosts+
                         self.ghostSnake.ghostTrain)

        for ghost in ghostsToCheck:
            ghost.color = (blueRGBTuple)

    #Makes every ghost it's original color
    def setGhostColorBack(self):
        ghostsToCheck = (self.leftGhosts+self.rightGhosts+
                         self.ghostSnake.ghostTrain)

        for ghost in ghostsToCheck:
            ghost.color = ghost.originalColor

    def checkForDotsEaten(self):
        #Remove from right half first
        #Use return because pac-man can only eat one dot at a time
        for dot in self.rightDots:
            if(dot.location == self.pacMan.location):
                self.rightDots.remove(dot)

                if(dot.pellet == True):
                    self.pelletTimer = self.pelletConstant
                    self.setGhostColorBlue()

                self.score += 10*self.speed
                self.scoreStreak += 10
                self.remove(dot)
                return

        for dot in self.leftDots:
            if(dot.location == self.pacMan.location):
                self.leftDots.remove(dot)

                if(dot.pellet == True):
                    self.pelletTimer = self.pelletConstant
                    self.setGhostColorBlue()

                self.score += 10*self.speed
                self.scoreStreak += 10
                self.remove(dot)
                return

    #makes sure turns happen correctly, and allows "premoving"
    def moveHandler(self,dt):
        bdx,bdy = (self.pacMan.bdx,self.pacMan.bdy)
        bx,by = self.pacMan.location

        if (self.directionToMove == "down" and 
        (by+1 < 0 or by+1 >= len(self.board) or self.board[by+1][bx] == "e")):
            self.currentDirection = self.directionToMove
            self.directionToMove = None
            self.pacMan.bdx = 0
            self.pacMan.bdy = 1
            self.pacMan.rotation = 270

        elif (self.directionToMove == "up" and 
        (by-1 < 0 or by-1 >= len(self.board) or self.board[by-1][bx] == "e")):
            self.currentDirection = self.directionToMove
            self.directionToMove = None
            self.pacMan.bdx = 0
            self.pacMan.bdy = -1
            self.pacMan.rotation = 90

        elif (self.directionToMove == "left" and 
        (bx-1 < 0 or bx-1 >= len(self.board[0]) or self.board[by][bx-1] == "e")):
            self.currentDirection = self.directionToMove
            self.directionToMove = None
            self.pacMan.bdx = -1
            self.pacMan.bdy = 0
            self.pacMan.rotation = 0

        elif (self.directionToMove == "right"and 
        (bx+1 < 0 or bx+1 >= len(self.board[0]) or self.board[by][bx+1] == "e")):
            self.currentDirection = self.directionToMove
            self.directionToMove = None
            self.pacMan.bdx = 1
            self.pacMan.bdy = 0
            self.pacMan.rotation = 180

        if(self.pacMan.location[1]+self.pacMan.bdy < 0 or
           self.pacMan.location[1]+self.pacMan.bdy >= len(self.board) or
           self.pacMan.location[0]+self.pacMan.bdx < 0 or
           self.pacMan.location[0]+self.pacMan.bdx >= len(self.board[0]) or
           self.board[self.pacMan.location[1]+self.pacMan.bdy][self.pacMan.location[0]+self.pacMan.bdx] == "e"):
           self.pacMan.move(self.board,self.cellSize,dt)

    def on_key_press(self,key,modifiers):
        self.keys_pressed.add(key)
        self.changeDirection()

    def on_key_release(self,key,modifiers):
        if(key in self.keys_pressed): #Let other functions mess with keys
            self.keys_pressed.remove(key)

    def checkForExtraLives(self):
        self.expectedExtraLives = self.score // self.extraLivesCutoff

        if(self.expectedExtraLives > self.livesScoreCounter):
            self.livesScoreCounter += 1
            self.lives += 1

    def gameOver(self):
        gameOverLabel = cocos.text.Label('GAME OVER!',
        font_name='Arial',font_size=64,anchor_x='center', anchor_y='center')

        finalScoreText = cocos.text.Label("Final Score: %d" % self.score,
        font_name='Arial',font_size=32,anchor_x='center', anchor_y='center')

        gameOverLabel.position = (550,370)
        finalScoreText.position = (550,300)

        self.add(gameOverLabel); self.add(finalScoreText)

        #Crashes sometimes for no particular reason.
        #Sometimes elements get removed prematurely by the module
        try:
            self.remove(self.pacMan)
            self.remove(self.scoreText);
            self.remove(self.livesLabel)
            self.remove(self.scoreLabel)
            self.remove(self.speedText)
            self.remove(self.speedLabel)
            self.remove(self.pelletLabel)
        except: pass
        
        self.pause_scheduler()


    #Made from tutorials found at:
    #http://python.cocos2d.org/doc/programming_guide/tiled_map.html
    def update(self,dt):
        self.changeDirection()
        self.moveHandler(dt)
        self.ghostSnake.move(self.board,self.pacMan.location)

        for ghost in (self.leftGhosts+self.rightGhosts):
            pelletActive = self.pelletTimer > 0
            ghost.update(self.pacMan.location,pelletActive)

        if(self.pelletTimer <= 0):
            self.leftGhosts=self.ghostSnake.addAdjacentGhosts(self.leftGhosts)
            self.rightGhosts=self.ghostSnake.addAdjacentGhosts(self.rightGhosts)
            self.ghostSnake.moveGhosts(self.board,self.cellSize)

        self.checkForDotsEaten()

        self.checkForLeftClear()
        self.checkForRightClear()

        self.checkIfLeftFruitEaten()
        self.checkIfRightFruitEaten()

        self.scoreText.element.text = str(self.score)
        self.speedText.element.text = str(self.speed)
        self.checkGhostCollision()

        self.changeSpeed()
        if(self.pelletTimer > 0):
            self.pelletTimer -= 1
            if(self.pelletTimer == 0):
                self.setGhostColorBack()
                self.gracePeriod = 10

        self.pelletLabel.element.text = 'Power-Up: %d' % self.pelletTimer
        self.livesLabel.element.text = 'Lives: %d' % self.lives
        self.checkForExtraLives()
        if(self.lives <= -1):self.gameOver()
        if(self.gracePeriod > 0): self.gracePeriod -= 1

#Random generation algorithm inspired by write up at
#http://stackoverflow.com/questions/12225981/how-to-create-a-random-pacman-maze
    @staticmethod
    def generateBoardHalf(side):
        #Side is either "right" or "left". If right, then just mirror
        #Will randomly generate a 17x12 half-maze
            
        #e means empty, s means solid, r means random(determined by algorithm)
        starterHalf = [
        ['s','s','s','s','s','s','s','s','s','s','s','s'],
        ['s','s','r','s','r','s','r','s','r','s','r','s'],
        ['s','s','e','r','e','r','e','r','e','r','e','r'],
        ['s','s','r','s','r','s','r','s','r','s','r','s'],
        ['s','s','e','r','e','r','e','r','e','r','e','r'],
        ['s','s','r','s','r','s','r','s','r','s','r','s'],
        ['s','s','e','r','e','r','e','r','e','r','e','r'],
        ['s','s','r','s','r','s','r','s','r','s','r','s'],
        ['s','s','e','r','e','r','e','r','e','r','e','r'],
        ['s','s','r','s','r','s','r','s','r','s','r','s'],
        ['s','s','e','r','e','r','e','r','e','r','e','r'],
        ['s','s','r','s','r','s','r','s','r','s','r','s'],
        ['s','s','e','r','e','r','e','r','e','r','e','r'],
        ['s','s','r','s','r','s','r','s','r','s','r','s'],
        ['s','s','e','r','e','r','e','r','e','r','e','r'],
        ['s','s','r','s','r','s','r','s','r','s','r','s'],
        ['s','s','s','s','s','s','s','s','s','s','s','s'],
        ]
        directionsToCheck = [(1,0),(0,1),(0,-1),(-1,0)]
        rows,cols = len(starterHalf),len(starterHalf[0])
        for row in range(rows):
            for col in range(cols):
                if(starterHalf[row][col] == 'e'):
                    solidCount = GameLayer.checkSpot(row,col,starterHalf)
                    for (dx,dy) in directionsToCheck:
                        nextX = col+dx
                        nextY = row+dy
                        #Can only replace r's on the board
                        if(GameLayer.outOfRange(nextX,nextY,starterHalf) or
                            starterHalf[nextY][nextX] != "r"):
                            continue

                        #If too many solids, make an empty
                        elif(solidCount >= 2 or random.randint(0,1) == 0 or
                    GameLayer.checkSpot(nextX+dx,nextY+dy,starterHalf) >= 2):
                            starterHalf[nextY][nextX] = "e0"
                            #Replace with 'e' at the end

                        else:
                            starterHalf[nextY][nextX] = "s"
                            solidCount += 1

        for row in range(rows):
            for col in range(cols):
                if(starterHalf[row][col] == "e0"): starterHalf[row][col] = 'e'

        finalBoard = GameLayer.edgeChecker(starterHalf)

        if(side == 'left'): return finalBoard
        else:
            for row in range(len(finalBoard)):
                finalBoard[row] = finalBoard[row][::-1]
                #Mirrors the board for the right side
        return finalBoard

    @staticmethod
    def outOfRange(x,y,board):
        if(y < 0 or y >= len(board) or
            x < 0 or x >= len(board[0])): return True
        else: return False

    #Returns number of solids around a specific spot on the board
    @staticmethod
    def checkSpot(x,y,board):
        if(GameLayer.outOfRange(x,y,board) or 
            board[y][x] != 'e'): return 0
        directionsToCheck = [(1,0),(-1,0),(0,1),(0,-1)]
        solidCount = 0 #Count all solids surrounding this tile
        for (dx,dy) in directionsToCheck:
            nextX = x+dx
            nextY = y+dy
            if(GameLayer.outOfRange(nextX,nextY,board)): continue
            elif(board[nextY][nextX] == 's'): solidCount += 1
        return solidCount

    #Makes holes on edges
    @staticmethod
    def edgeChecker(board):

        #Make holes on top
        topRow = 1
        bottomRow = len(board)-2

        col = 0
        hollowRows = [4,12]
        #Make holes in back of maze
        for row in hollowRows:
            col = 0
            while (board[row][col] == 's'):
                board[row][col] = 'e'
                col += 1

        #Make holes in top and bottom of maze
        for col in range(len(board[topRow])):
            if(board[topRow][col] == 'e' and board[bottomRow][col] == 'e'):
                board[topRow-1][col] = board[bottomRow+1][col] = 'e'
            else: board[topRow][col] = board[bottomRow][col] = 's'
        
        for row in range(2,len(board)-1):
            for col in range(1,len(board[0])):

                if(board[row][col]=='e'):
                    solidCount = GameLayer.checkSpot(col,row,board)
                    directions = [(1,0),(0,1),(0,-1),(-1,0)]

                    while(solidCount > 2 and len(directions) > 0):
                        (dx,dy) = random.choice(directions)
                        newX,newY = col+dx,row+dy

                        if(((GameLayer.checkSpot(newX+dx,newY+dy,
                            board) and board[newY+dy][newX+dx] == "e") or
                            newX+dx > len(board)) and board[newY][newX] == 's'):

                            board[newY][newX] = 'e'
                            solidCount -= 1

                        directions.remove((dx,dy))

        return board

    def rightMazeReplacer(self,oldBoard):
        newRightHalf = GameLayer.generateBoardHalf('right')
        board = oldBoard.copy()
        colStart = 19
        rows = len(board)
        for row in range(rows):
            board[row] = board[row][0:colStart] + newRightHalf[row]
        return board

    def leftMazeReplacer(self,oldBoard):
        newLeftHalf = GameLayer.generateBoardHalf('left')
        board = oldBoard.copy()
        colStop = 12
        rows = len(board)
        for row in range(rows):
            board[row] = newLeftHalf[row] + board[row][colStop:]
        return board

    #Checks if a location has a dot in it
    @staticmethod
    def dotAtLocation(dotList,targetLoc):
        for dot in dotList:
            if(targetLoc == dot.location):
                return True

        return False

    #Checks if a ghost is at a specific location
    #Returns the Ghost object if there, otherwise none
    @staticmethod
    def ghostAtLocation(ghostList,targetLocation):
        for ghost in ghostList:
            if(ghost.location == targetLocation): return ghost
        return None


    def mazeEntityPlacer(self,side):
        if(side == 'right'):
            leftBound = 19
            rightBound = len(self.board[0])-1
            entranceCols = [leftBound,rightBound]
        elif(side == 'left'):
            leftBound = 0
            rightBound = 11
            entranceCols = [rightBound,leftBound]

        rows,cols = len(self.board),len(self.board[0])
        entrance = None
        oppositeDir = None
        #Entrance for the recursive algorithm that places dots/ghosts

        for row in range(rows):
            for col in entranceCols:
                if(self.board[row][col] == 'e'):
                    entrance = (col,row)
                    if(col in [11,cols-1]): oppositeDir = (1,0)
                    elif(col in [19,0]): oppositeDir = (-1,0)
                    break

        if(entrance == None): return None #If no entrances, flip out
        #Places entities in the maze recursively
        #Can go over itself
        def mazePlacer(location,oppositeDir,leftBound,rightBound,
            board,place=True,dots=[],ghosts=[],length=0):
            (x,y) = location

            #Off back or front means stop, we've hit an exit
            if(x < leftBound or x > rightBound or length == 30):
                return dots,ghosts
            #Also base case ^

            #Only place if instructed to
            if(place == True):
                pellet = False
                if(random.randint(1,20) == 1): pellet = True
                px,py = self.cells[y][x].center
                dots += [Dot(pellet,px,py,x,y)]

            possibleLocations = []
            possibleDirections = [(1,0),(0,1),(0,-1),(-1,0)]
            possibleDirections.remove(oppositeDir)

            for (dx,dy) in possibleDirections:
                newX,newY = x+dx,y+dy

                #Wrap around when moving in Y is allowed
                if(newY < 0): newY = len(board)-1
                elif(newY >= len(board)): newY = 0
                if(newX < 0 or newX >= len(board[0])): continue

                if(board[newY][newX] == "e"):
                    possibleLocations += [((newX,newY),(-dx,-dy))]
                    #Store opposite direction

            while (len(possibleLocations) > 0):
                candidateSpot,oppositeDir = random.choice(possibleLocations)
                possibleLocations.remove((candidateSpot,oppositeDir))

                #A dot in the candidate location
                if(GameLayer.dotAtLocation(dots,candidateSpot) == True):
                    if(place == False): break #Don't not place twice
                    place = False
                    length -= 1 #Don't add to length if not placing
                else: place = True #No dot in candidate location

                #If going over a placed ghost, remove it
                ghostToRemove = GameLayer.ghostAtLocation(ghosts,candidateSpot)
                if(ghostToRemove != None): ghosts.remove(ghostToRemove)

                #Place ghosts in other places if at junction
                for ghostLoc in possibleLocations:
                    ghostX,ghostY = ghostLoc[0]
                    px,py = self.cells[ghostY][ghostX].center
                    ghosts += [Ghost("ghostPlaceholder.png",px,py,ghostX,ghostY)]

                return mazePlacer(candidateSpot,oppositeDir,leftBound,rightBound,board,place,dots,ghosts,length+1)

            #At end means no candidate spots! So we're done
            return dots,ghosts

        return mazePlacer(entrance,oppositeDir,leftBound,rightBound,self.board)

    #Converts board to cells module uses
    @staticmethod
    def boardConverter(board,cellSize):
        solidProperties={"top":True,"bottom":True,"left":True,"right":True,
                        "solid":True}
        emptyProperties={"top":False,"bottom":False,"left":False,"right":False,
                        "solid":False}
        fullTile = cocos.sprite.Sprite("fullTilePlaceholder.png")
        emptyTile = cocos.sprite.Sprite("emptyTilePlaceholder.png")

        result = [[] for i in range(len(board))]
        rows = len(board)
        for i in range(rows):
            for j in range(len(board[0])):
                if(board[i][j] == "s"): result[i] += [cocos.tiles.RectCell(j,
                        rows-i,cellSize,cellSize,solidProperties,fullTile)]
                else: result[i] += [cocos.tiles.RectCell(j,
                    rows-i,cellSize, cellSize,emptyProperties,emptyTile)]

        return result

    def makeGrid(self,cellSize):
        
        board = [
['s','s','e','s','e','s','e','s','e','s','s','s','e','s','s','s','s','s','e','s','s','s','e','s','s','s','e','s','s','s','s'],
['s','s','e','s','e','s','e','s','e','s','s','s','e','s','s','s','s','s','e','s','s','s','e','s','s','s','e','s','s','s','s'],
['s','s','e','e','e','e','e','s','e','e','e','e','e','s','s','s','s','s','e','e','e','e','e','s','e','e','e','e','e','s','s'],
['s','s','e','s','e','s','e','s','e','s','e','s','e','s','s','s','s','s','e','s','s','s','e','s','e','s','s','s','e','s','s'],
['e','e','e','s','e','e','e','e','e','s','e','e','e','e','e','e','e','e','e','e','e','e','e','s','e','e','e','s','e','e','e'],
['s','s','s','s','e','s','s','s','s','s','s','s','e','s','s','e','s','s','e','s','e','s','e','s','s','s','e','s','e','s','s'],
['s','s','e','e','e','e','e','s','e','e','e','e','e','e','e','e','e','e','e','s','e','e','e','e','e','e','e','s','e','s','s'],
['s','s','e','s','e','s','e','s','e','s','e','s','e','s','s','e','s','s','e','s','e','s','s','s','e','s','e','s','e','s','s'],
['s','s','e','e','e','e','e','e','e','s','e','e','e','e','e','e','e','e','e','s','e','e','e','s','e','s','e','e','e','s','s'],
['s','s','s','s','e','s','e','s','e','s','e','s','e','s','s','e','s','s','e','s','s','s','e','s','e','s','e','s','e','s','s'],
['s','s','e','e','e','e','e','e','e','s','e','e','e','e','e','e','e','e','e','e','e','e','e','e','e','e','e','e','e','s','s'],
['s','s','e','s','e','s','e','s','e','s','e','s','e','s','s','e','s','s','e','s','e','s','e','s','e','s','e','s','e','s','s'],
['e','e','e','e','e','s','e','e','e','e','e','e','e','e','e','e','e','e','e','s','e','e','e','e','e','e','e','s','e','e','e'],
['s','s','s','s','s','s','e','s','e','s','s','s','e','s','s','s','s','s','e','s','e','s','e','s','e','s','e','s','e','s','s'],
['s','s','e','e','e','e','e','s','e','e','e','e','e','s','s','s','s','s','e','s','e','e','e','e','e','s','e','e','e','s','s'],
['s','s','e','s','e','s','e','s','e','s','s','s','e','s','s','s','s','s','e','s','s','s','e','s','s','s','e','s','s','s','s'],
['s','s','e','s','e','s','e','s','e','s','s','s','e','s','s','s','s','s','e','s','s','s','e','s','s','s','e','s','s','s','s']
        ]
        board = self.rightMazeReplacer(self.leftMazeReplacer(board))
        finalCells = GameLayer.boardConverter(board,cellSize)

        return finalCells,board

def main():
    width,height = 1100,619
    cellSize = 35#width//cols
    cocos.director.director.init(width=width,height=height,fullscreen=False)
    cocos.director.director.run(cocos.scene.Scene(GameLayer(cellSize)))

main()