from flask import Flask, render_template, jsonify, request, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

app = Flask(__name__)

dictGames={}

def cleanUp():
	for room_name in dictGames.keys():
		print(datetime.datetime.now() - dictGames[room_name].lastAccessed)
		if datetime.datetime.now() - dictGames[room_name].lastAccessed > datetime.timedelta(minutes=15):
			print("Cleaning up room " + room_name)
			dictGames.pop(room_name)

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
		self.turnUpdate = False
		self.winner = -1
		self.newGame = 0 # 0: neutral, 1: restart game, -1: newGame rejected by player.

	def setOrderPlayer(self, playerIndex):
		self.gameStarted = True
		self.orderPlayer = playerIndex
		self.chooseRole = False
		self.playerTurn = playerIndex

	def turn_played(self, pos, color, playerIndex):
		if playerIndex == self.playerTurn:
			(i,j) = pos
			self.gameState[i][j] = color
			self.turnUpdate = [i,j,color]

			self.checkVictory()

		else:
			print("SOMETHING HAS GONE HORRIBLY WRONG")

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
			print("SHOULD NOT HAPPEN. ALERT ALERT.")
	def returnDict(self):
		return {key:value for key, value in self.__dict__.items() if not key.startswith('__') and not callable(key)}

@app.route('/')
def index():
   return render_template('index.html')

@app.route('/play', methods = ['POST', 'GET'])
def loadRoom():
	if request.method == 'GET':
		return redirect(url_for('index'))
	if request.method == 'POST':
		print("Room join/create request")

		req_room_name = request.form.get('room_name') # requested_room_name
		playerIndex = int(request.form.get('player_index'))

		if playerIndex == 0:
			if req_room_name in dictGames.keys():
				return render_template('index.html', error_message="Room already exists.")

			else:
				newGame = Game()
				newGame.playerNames[0] = request.form.get('player_name')
				newGame.playerLogOnStatus[0] = True
				newGame.room_name = req_room_name
				newGame.lastAccessed = datetime.datetime.now()
				dictGames[req_room_name] = newGame

				print("Current Games Keys")
				print(dictGames.keys())

				return render_template('gameplay.html', gameConfig=newGame, player=0)

		if playerIndex == 1:
			if req_room_name not in dictGames.keys():
				return render_template('index.html', error_message="Room doesn't exist.")

			else:
				if dictGames[req_room_name].playerLogOnStatus[1] == False:
					dictGames[req_room_name].playerNames[1] = request.form.get('player_name')
					dictGames[req_room_name].playerLogOnStatus[1] = True
					dictGames[req_room_name].lastAccessed = datetime.datetime.now()
					dictGames[req_room_name].chooseRole = True

					return render_template('gameplay.html', gameConfig=dictGames[req_room_name], player=1)

				else:
					return render_template('index.html', error_message="Room full.")

	else:
		return render_template('gameplay.html')

@app.route('/pregame', methods = ['POST'])
def pre_game():
	room_name = request.form.get('room_name')
	playerIndex = int(request.form.get('player_index'))

	if room_name in dictGames.keys():
		dictGames[room_name].lastAccessed = datetime.datetime.now()
		if playerIndex == 0:
			return jsonify(validRoom=True, gameStarted=dictGames[room_name].gameStarted, chooseRole=dictGames[room_name].chooseRole, player_1_name=dictGames[room_name].playerNames[1])
		elif playerIndex == 1:
			return jsonify(validRoom=True, gameStarted=dictGames[room_name].gameStarted, orderPlayer=dictGames[room_name].orderPlayer)
	else:
		return jsonify(validRoom=False)

@app.route('/role_chosen', methods = ['POST'])
def role_chosen():
	room_name = request.form.get('room_name')
	playerIndex = int(request.form.get('player_index'))

	if room_name in dictGames.keys():
		dictGames[room_name].lastAccessed = datetime.datetime.now()

		if playerIndex == 0:
			player_0_role = int(request.form.get('player_0_role'))
			
			dictGames[room_name].setOrderPlayer(player_0_role) # Should basically use the inverse permutation, but happy coincidence that both permutations of [2] are their own inverses.

@app.route('/turn_wait', methods = ['POST'])
def turn_wait():
	room_name = request.form.get('room_name')
	playerIndex = int(request.form.get('player_index'))

	if room_name in dictGames.keys():
		dictGames[room_name].lastAccessed = datetime.datetime.now()

		turn = dictGames[room_name].turnUpdate

		if turn and playerIndex != dictGames[room_name].playerTurn:
			dictGames[room_name].playerTurn = playerIndex
			dictGames[room_name].turnUpdate = False

			if dictGames[room_name].gameOver:
				if dictGames[room_name].winner == playerIndex:
					message = "You have won!"
				else:
					message = "You have lost :("

				return jsonify(validRoom=True, gameOver=dictGames[room_name].gameOver, gameOverMessage=message, turn=turn, score=dictGames[room_name].score)

			else:
				return jsonify(validRoom=True, gameOver=dictGames[room_name].gameOver, turn=turn)

		else:
			return jsonify(validRoom=True)

@app.route('/turn_played', methods = ['POST'])
def turn_played():
	room_name = request.form.get('room_name')
	playerIndex = int(request.form.get('player_index'))

	cell = request.form.get('cell')
	color = int(request.form.get('color'))

	if room_name in dictGames.keys():
		dictGames[room_name].lastAccessed = datetime.datetime.now()
		(i,j) = (int(cell[5]), int(cell[7]))

		dictGames[room_name].turn_played((i,j), color, playerIndex)

		if dictGames[room_name].gameOver:
			if dictGames[room_name].winner == playerIndex:
				message = "You have won!"
			else:
				message = "You have lost :("

			return jsonify(validRoom=True, gameOver=dictGames[room_name].gameOver, gameOverMessage=message, score=dictGames[room_name].score)

		else:
			return jsonify(validRoom=True, gameOver=dictGames[room_name].gameOver)

@app.route('/new_game', methods = ['POST'])
def new_game():
	room_name = request.form.get('room_name')
	playerIndex = int(request.form.get('player_index'))
	playAgain = request.form.get('new_game_bool')

	if playAgain == 'true':
		if room_name in dictGames.keys():
		
			dictGames[room_name].gameState = [ [-1 for i in range(6)] for j in range(6)]
			dictGames[room_name].gameOver = False
			dictGames[room_name].orderPlayer = 1 - dictGames[room_name].orderPlayer
			dictGames[room_name].lastAccessed = datetime.datetime.now()

			dictGames[room_name].gameStarted = True
			dictGames[room_name].playerTurn = dictGames[room_name].orderPlayer
			dictGames[room_name].turnUpdate = False
			dictGames[room_name].winner = -1
			dictGames[room_name].newGame = 1

			return jsonify(validRoom=True, orderPlayer=dictGames[room_name].orderPlayer)

		else:
			return jsonify(validRoom=False)			

	elif playAgain == 'false':
		dictGames[room_name].newGame = -1

@app.route('/new_game_wait', methods = ['POST'])
def new_game_wait():
	#validRoom, newGame, orderPlayer

	room_name = request.form.get('room_name')
	playerIndex = int(request.form.get('player_index'))

	if dictGames[room_name].newGame == 1:
		dictGames[room_name].newGame = 0
		return jsonify(validRoom=True, newGame=1, orderPlayer=dictGames[room_name].orderPlayer)
	else:
		return jsonify(validRoom=True, newGame=dictGames[room_name].newGame, orderPlayer=dictGames[room_name].orderPlayer)

if __name__ == '__main__':
	print("BackgroundScheduler started")
	backgroundCleanup = BackgroundScheduler()
	backgroundCleanup.add_job(func=cleanUp, trigger="interval", hours=1)
	backgroundCleanup.start()