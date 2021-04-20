from flask import Flask, render_template, jsonify, request, redirect, url_for
import datetime
import os
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app)

dictGames={}

class Game:
    def __init__(self):
        self.room_name = ""
        self.gameState = [ [-1 for i in range(6)] for j in range(6)]
        self.gameOver = False
        self.playerNames = ["", ""]
        self.playerLogOnStatus = [False, False]
        self.orderPlayer = -1
        self.lastAccessed = ""
        self.score = [0,0]

        self.chooseRole = False # Whether to launch pop-up
        self.gameStarted = False
        self.playerTurn = -1
        #self.turnUpdate = False
        self.winner = -1
        self.newGame = 0 # 0: neutral, 1: restart game, -1: newGame rejected by player.

    def setOrderPlayer(self, playerIndex):
        self.gameStarted = True
        self.orderPlayer = playerIndex
        self.chooseRole = False
        self.playerTurn = playerIndex

    def createGame(self, player_name, room_name):
        self.room_name = room_name
        self.playerNames[0] = player_name
        self.playerLogOnStatus[0] = True
        self.lastAccessed = datetime.datetime.now()

    def joinGame(self, player_name):
        self.playerNames[1] = player_name
        self.playerLogOnStatus[1] = True
        self.lastAccessed = datetime.datetime.now()
        self.chooseRole = True

    def turn_played(self, pos, color, playerIndex):
        (i,j) = pos

        self.lastAccessed = datetime.datetime.now()

        if playerIndex == self.playerTurn and self.gameState[i][j] == -1:
            self.gameState[i][j] = color
            self.playerTurn = 1 - self.playerTurn
            #self.turnUpdate = [i,j,color]

            self.checkVictory()

        else:
            print("SOMETHING HAS GONE HORRIBLY WRONG: " + str(pos) + ", " + str(playerIndex) + ", " + str(self.playerTurn) + ", " + str(self.gameState[i][j]))

    def checkVictory(self):
        foundWin = False

        for i in range(6):
            foundWin = foundWin or self.checkWin(self.gameState[i])
            foundWin = foundWin or self.checkWin([self.gameState[j][i] for j in range(6)])

        foundWin = foundWin or self.checkWin([self.gameState[i][i] for i in range(6)]) 
        foundWin = foundWin or self.checkWin([self.gameState[5-i][i] for i in range(6)])

        foundWin = foundWin or self.checkWin([self.gameState[i][i+1] for i in range(5)])
        foundWin = foundWin or self.checkWin([self.gameState[i+1][i] for i in range(5)])
        foundWin = foundWin or self.checkWin([self.gameState[5-i][i+1] for i in range(5)])
        foundWin = foundWin or self.checkWin([self.gameState[4-i][i] for i in range(5)])

        if foundWin:
            self.gameOver = True
            self.winner = self.orderPlayer
            self.score[self.orderPlayer] += 1

        else:
            checkAllFilled = True

            for i in range(6):
                for j in range(6):
                    if self.gameState[i][j] not in [1, 2]:
                        checkAllFilled = False

            if checkAllFilled:
                self.gameOver = True
                self.winner = 1 - self.orderPlayer
                self.score[1 - self.orderPlayer] += 1

    def checkWin(self, arr):
        if len(arr) == 5:
            return (arr == [1] * 5) or (arr == [2] * 5)

        elif len(arr) == 6:
            return (self.checkWin(arr[:-1]) or self.checkWin(arr[1:]))

        else:
            print("SHOULD NOT HAPPEN. ALERT ALERT: " + str(len(arr)))

    def surrender(self, playerIndex):
        self.lastAccessed = datetime.datetime.now()
        self.gameOver = True
        self.winner = 1 - playerIndex
        self.score[1 - playerIndex] += 1

    def returnDict(self):
        return {key:value for key, value in self.__dict__.items() if not key.startswith('__') and not callable(key)}

    def resetEverything(self):
        self.gameState = [ [-1 for i in range(6)] for j in range(6)]
        self.gameOver = False
        self.orderPlayer = 1 - self.orderPlayer
        self.lastAccessed = datetime.datetime.now()
        self.gameStarted = True
        self.playerTurn = self.orderPlayer
        #self.turnUpdate = False
        self.winner = -1
        self.newGame = 1

@app.route('/')
def index():
   return render_template('index.html')

@app.route('/play', methods = ['POST', 'GET'])
def loadRoom():
    if request.method == 'GET':
        req_room_name = request.args.get("room")

        if req_room_name == None:
            return render_template('index.html', error_message="Unknown request.")

        # else:
            # Have to implement an input feature that takes just player name. 

    if request.method == 'POST':

        req_room_name = request.form.get('room_name') # requested_room_name
        #send(username + ' has entered the room.', room=room)

        playerIndex = int(request.form.get('player_index'))

        if playerIndex == 0:
            print("Room create request: " + str(req_room_name))

            if req_room_name in dictGames.keys() and (datetime.datetime.now() - dictGames[room_name].lastAccessed < datetime.timedelta(minutes=10)):
                return render_template('index.html', error_message="Room already exists.")

            else:
                # Possible memory leakage, should delete expired rooms here.
                newGame = Game()
                newGame.createGame(request.form.get('player_name'), req_room_name)
                dictGames[req_room_name] = newGame

                print("Current Games Keys:")
                print(dictGames.keys())

                return render_template('gameplay.html', gameConfig=newGame, player=0)

        if playerIndex == 1:
            print("Room join request: " + str(req_room_name))

            if req_room_name not in dictGames.keys():
                return render_template('index.html', error_message="Room doesn't exist.")

            else:
                if dictGames[req_room_name].playerLogOnStatus[1] == False:
                    dictGames[req_room_name].joinGame(request.form.get('player_name'))

                    return render_template('gameplay.html', gameConfig=dictGames[req_room_name], player=1)
                
                else:
                    return render_template('index.html', error_message="Room full.")  

    else:
        return render_template('index.html', error_message="Unknown request.")

@socketio.on('connect')
def test_connect():
    pass

@socketio.on('room')
def room_join(data):
    join_room(data['room'])

    if data['playerIndex'] == 1:
        emit('user_joined', dictGames[data['room']].playerNames, room=data['room'])

@socketio.on('role_chosen')
def role_chosen(data):
    dictGames[data['room']].setOrderPlayer(data['playerIndex'] ^ data['roleChosen'])  # it works. order -> 0, chaos -> 1. ^ is bitwise xor.
    emit('role_chosen', dictGames[data['room']].orderPlayer, room=data['room'])

@socketio.on('turn_played')
def turn_played(data):
    room_name = data['room']
    playerIndex = int(data['playerIndex'])
    cell = data['cell']
    color = int(data['color'])

    if room_name in dictGames.keys():
        (i,j) = (int(cell[5]), int(cell[7])) # passing cell-id. By the naming convention, their co-ordinates are stored as the 5th and 7th char in string.

        dictGames[room_name].turn_played((i,j), color, playerIndex)

        returnParams = {}
        returnParams['cell'] = cell
        returnParams['color'] = color
        returnParams['gameOver'] = dictGames[room_name].gameOver

        if not dictGames[room_name].gameOver:
            returnParams['playerTurn'] = dictGames[room_name].playerTurn         

        emit('turn_played', returnParams, room=data['room'])

        if dictGames[room_name].gameOver: # Repeated clause because want to emit turn_played before game_over, but only want to include playerTurn if not gameOver.
            emit('game_over', {'winner': dictGames[room_name].winner, 'score': dictGames[room_name].score}, room=data['room'])

@socketio.on('play_again')
def play_again(data):
    room_name = data['room']
    playerIndex = int(data['playerIndex'])
    playAgain = data['newGameBool']

    print(type(playAgain))
    print(playAgain)

    if room_name in dictGames.keys():
        if playAgain:
            dictGames[room_name].resetEverything()

            emit('play_again', dictGames[data['room']].orderPlayer, room=data['room'])

        else:
            dictGames[room_name].newGame = -1

@socketio.on('surrender')
def surrender(data):
    room_name = data['room']
    playerIndex = int(data['playerIndex'])

    if room_name in dictGames.keys():
        dictGames[room_name].surrender(playerIndex)

        emit('game_over', {'winner': dictGames[room_name].winner, 'score': dictGames[room_name].score}, room=data['room'])

@socketio.on('send_message')
def send_message(data):
    room_name = data['room']
    playerIndex = int(data['playerIndex'])

    if room_name in dictGames.keys():
        messageString = "<b>" + dictGames[room_name].playerNames[playerIndex] + ": </b> " + data['text']
        emit('send_message', {'text': messageString}, room=data['room'])

@app.route('/clean_up', methods = ['GET'])
def serverCleanUp():
    cleanUp()

if __name__ == '__main__':
    socketio.run(app)
