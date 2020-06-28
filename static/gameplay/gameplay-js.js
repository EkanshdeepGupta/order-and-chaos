

function setPlayerLoading(player_index) {
	document.getElementById('loading-div-' + player_index.toString()).innerHTML = '<img id="loading-gif" height="" src="' + loading_gif_url + '">';

	$("#loading-gif").css('height', '30px');
}

function removePlayerLoading(player_index) {
	document.getElementById('loading-div-' + player_index.toString()).innerHTML = '';
}

function xmlrequestFormData() {
	var params = new FormData();
	params.append('room_name', room_name);
	params.append('player_index', myPlayerIndex.toString());

	return params;
}

function reStyleCells(stylesheet){
   $('#cell-styles').attr("href",stylesheet);
}

function beforeGameStartLoop(){ // Loop for when player 0 logs on and is waiting for player 1 to log on.
	var myRequest = new XMLHttpRequest();
	var params = xmlrequestFormData();

	myRequest.open('POST', '/pregame', true); 

	myRequest.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var myResponseJSON = JSON.parse(this.responseText);

			if (myResponseJSON.validRoom && !myResponseJSON.gameStarted) {

				if (myResponseJSON.chooseRole) {
					document.getElementById('player-1-name').innerHTML = myResponseJSON.player_1_name;
					document.getElementById('score').innerHTML = "Score: 0-0";
					chooseRolePopUp();
				}

				else {
					setTimeout(beforeGameStartLoop, 300);
				}
			}
		}

		else if (this.readyState == 4) {
			setTimeout(beforeGameStartLoop, 300);
		}
	}

	myRequest.send(params);
}

function waitGameStartLoop() { // Loop for when player 1 logs on and is waiting for player 0 to choose starting role.
	var myRequest = new XMLHttpRequest();
	var params = xmlrequestFormData();

	myRequest.open('POST', '/pregame', true); 

	myRequest.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var myResponseJSON = JSON.parse(this.responseText);

			if (myResponseJSON.validRoom) {
				if (myResponseJSON.gameStarted) {
					document.getElementById('score').innerHTML = "Score: 0-0";

					if (myResponseJSON.orderPlayer == 0) {
						document.getElementById("player-0-role").innerHTML = 'Order';
						document.getElementById("player-1-role").innerHTML = 'Chaos';
						turnWait();
					}

					else if (myResponseJSON.orderPlayer == 1){
						document.getElementById("player-0-role").innerHTML = 'Chaos';
						document.getElementById("player-1-role").innerHTML = 'Order';
						removePlayerLoading(0);
						myTurn();
					}
				}

				else {
					setTimeout(waitGameStartLoop, 300);
				}
			}
		}

		else if (this.readyState == 4) {
			setTimeout(waitGameStartLoop, 300);
		}
	}

	myRequest.send(params);
}

function chooseRolePopUp() {
	removePlayerLoading(1);
	document.getElementById("chooseRole").style.display = "block";
	document.getElementById("chooseRole").style.zIndex = 15;
	overlay();
}

function roleChosen(roleIndex) {
	document.getElementById("chooseRole").style.display = "none";
	removeOverlay()

	var myRequest = new XMLHttpRequest();
	var params = xmlrequestFormData();
	params.append('player_0_role', roleIndex.toString());

	myRequest.open('POST', '/role_chosen', true);

	myRequest.onreadystatechange = function() {
		if (this.readyState == 4 && this.status != 200) {
			this.open('POST', '/role_chosen', true);
			this.send(params);
		}
	}

	myRequest.send(params);

	if (roleIndex == 0) {
		document.getElementById("player-0-role").innerHTML = 'Order';
		document.getElementById("player-1-role").innerHTML = 'Chaos';

		myTurn();
	}

	else {
		document.getElementById("player-0-role").innerHTML = 'Chaos';
		document.getElementById("player-1-role").innerHTML = 'Order';

		setPlayerLoading(1);
		turnWait();
	}
}

function myTurn() {
	$('.button').css("display", "inline");
	removePlayerLoading(1 - myPlayerIndex);

	$('.game-tile-0').css('cursor', 'pointer');
}

function redTurn() {
	$('.game-tile').unbind('click');
	$('.game-tile-0').click(function() {
		turnPlayed(this, 1);
	});

	$('.game-tile-0').hover(function() {
		$(this).css("background", "#fac4bb");
	},
	function() {
		$(this).css("background", "");
	});
}

function blueTurn() {
	$('.game-tile').unbind('click');
	$('.game-tile-0').click(function() {
		turnPlayed(this, 2);
	});

	$('.game-tile-0').hover(function() {
		$(this).css("background", "#d1e3ff");
	},
	function() {
		$(this).css("background", "");
	});
}

function turnPlayed(elt, color) {
	$('.button').css("display", "none");
	$('#' + elt.id).css("background", ""); // to negate the hover background
	$('.game-tile').unbind('mouseenter mouseleave click');
	$('.game-tile').css('cursor', 'default');
	console.log(color);
	$('#' + elt.id).removeClass('game-tile-0').addClass('game-tile-' + color.toString());
	reStyleCells(cellStyle_url + '?v=' + new Date().getTime());
	
	var myRequest = new XMLHttpRequest();
	var params = xmlrequestFormData();

	params.append('cell', elt.id);
	params.append('color', color.toString());

	myRequest.open('POST', '/turn_played', true);

	myRequest.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var myResponseJSON = JSON.parse(this.responseText);

			if (myResponseJSON.validRoom) {
				if (myResponseJSON.gameOver) {
					document.getElementById('score').innerHTML = "Score: " + myResponseJSON.score[0].toString() + "-" + myResponseJSON.score[1].toString();
					alert(myResponseJSON.gameOverMessage);
					newGamePopUp();
				}

				else {
					setPlayerLoading(1 - myPlayerIndex);
					turnWait();
				} 
			}
		}

		else if (this.readyState == 4) {
			this.open('POST', '/turn_played', true);
			this.send(params);
		}

	}

	myRequest.send(params);
}

function turnWait() {
	var myRequest = new XMLHttpRequest();

	var params = xmlrequestFormData();

	myRequest.open('POST', '/turn_wait', true); 

	myRequest.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var myResponseJSON = JSON.parse(this.responseText);
			var turn = myResponseJSON.turn;

			if (myResponseJSON.validRoom) {
				if (myResponseJSON.gameOver) {
					document.getElementById('score').innerHTML = "Score: " + myResponseJSON.score[0].toString() + "-" + myResponseJSON.score[1].toString();
					removePlayerLoading(1 - myPlayerIndex);

					alert(myResponseJSON.gameOverMessage);
					newGameWait();
				}

				else if (turn) {
					$('#cell-' + turn[0].toString() + '-' + turn[1].toString()).removeClass('game-tile-0').addClass('game-tile-' + turn[2].toString());

					reStyleCells(cellStyle_url + '?v=' + new Date().getTime());

					myTurn();
				}

				else {
					setTimeout(turnWait, 300);
				}
			}	
		}

		else if (this.readyState == 4) {
			setTimeout(turnWait, 300);
		}

	}

	myRequest.send(params);

}

function newGameWait() {
	var myRequest = new XMLHttpRequest();
	var params = xmlrequestFormData();

	myRequest.open('POST', '/new_game_wait', true);

	myRequest.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var myResponseJSON = JSON.parse(this.responseText);

			if (myResponseJSON.validRoom) {
				if (myResponseJSON.newGame == 1) {
					newGameClientCleanUp(myResponseJSON.orderPlayer);
				}

				else if (myResponseJSON.newGame == 0) {
					setTimeout(newGameWait, 300);
				}

				else if (myResponseJSON.newGame == -1) {
					finish();
				}
			}
		}

		else if (this.readyState == 4) {
			setTimeout(newGameWait, 300);
		}
	}

	myRequest.send(params);
}

function newGamePopUp() {
	document.getElementById("newGame").style.display = "block";
	document.getElementById("newGame").style.zIndex = 15;
	overlay();
}

function newGame(playagain) {
	document.getElementById("newGame").style.display = "none";
	removeOverlay();

	var myRequest = new XMLHttpRequest();
	var params = xmlrequestFormData();
	params.append('new_game_bool', playagain.toString());

	myRequest.open('POST', '/new_game', true);

	if (playagain) {
		myRequest.onreadystatechange = function() {
			if (this.readyState == 4 && this.status == 200) {
				var myResponseJSON = JSON.parse(this.responseText);

				if (myResponseJSON.validRoom) {

					newGameClientCleanUp(myResponseJSON.orderPlayer);

				}
			}

			else if (this.readyState == 4) {
				myRequest.open('POST', '/new_game', true);
				this.send(params);
			}
		}
	}

	else {
		finish();
	}

	myRequest.send(params);
}

function finish() {

}

function newGameClientCleanUp(orderPlayer) {
	$('.game-tile-1').removeClass('game-tile-1').addClass('game-tile-0');
	$('.game-tile-2').removeClass('game-tile-2').addClass('game-tile-0');
	reStyleCells(cellStyle_url + '?v=' + new Date().getTime());

	document.getElementById("player-"+ orderPlayer.toString()+ "-role").innerHTML = 'Order';
	document.getElementById("player-"+ (1-orderPlayer).toString() +"-role").innerHTML = 'Chaos';

	if (orderPlayer == myPlayerIndex) {
		myTurn();
	}

	else {
		setPlayerLoading(1 - myPlayerIndex);
		turnWait();
	}
}

function surrender() {
	$('.button').css("display", "none");
	$('.game-tile').unbind('mouseenter mouseleave click');
	$('.game-tile').css('cursor', 'default');

	var myRequest = new XMLHttpRequest();

	var params = xmlrequestFormData();

	myRequest.open('POST', '/surrender', true); 

	myRequest.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var myResponseJSON = JSON.parse(this.responseText);

			if (myResponseJSON.validRoom) {
				if (myResponseJSON.gameOver) {
					document.getElementById('score').innerHTML = "Score: " + myResponseJSON.score[0].toString() + "-" + myResponseJSON.score[1].toString();
					alert(myResponseJSON.gameOverMessage);
					newGamePopUp();
				}

				else {
					setPlayerLoading(1 - myPlayerIndex);
					turnWait();
				} 
			}
		}

		else if (this.readyState == 4) {
			this.open('POST', '/surrender', true); 
			this.send(params);
		}

	}

	myRequest.send(params);

} 
