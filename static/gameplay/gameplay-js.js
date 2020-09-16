var socket;

function jsonData() { // Returns identifying state info
    return {room: room_name, playerIndex: myPlayerIndex};
}

$(document).ready(function(){

    socket = io('http://' + document.domain + ':' + location.port); //'http://' + document.domain + ':' + location.port
    socket.on('connect', function() {
        socket.emit('room', jsonData());
    });

    socket.on('user_joined', function(username) {
        document.getElementById('player-1-name').innerHTML = username[1];
        document.getElementById('score').innerHTML = "Score: 0-0";
        if (myPlayerIndex == 0) {
            chooseRolePopUp();  
        }
    });

    socket.on('role_chosen', function(orderPlayer) {
        document.getElementById("player-" + orderPlayer + "-role").innerHTML = 'Order';
        document.getElementById("player-" + (1 - orderPlayer) + "-role").innerHTML = 'Chaos';

        if (orderPlayer == myPlayerIndex) {
            myTurn();
        }
    });

    socket.on('turn_played', function(gameState) {
        $('#' + gameState.cell).removeClass('game-tile-0').addClass('game-tile-' + gameState.color.toString());
        reStyleCells(cellStyle_url + '?v=' + new Date().getTime()); // Reload the cell style-sheet. getTime() hack to prevent caching.

        removePlayerLoading(1 - myPlayerIndex); // will be executed pointlessly when the player who just played receives this event, but no harm.

        if (!gameState.gameOver && gameState.playerTurn == myPlayerIndex) { // If gameOver happens, then gameState won't have an object called playerTurn.
            myTurn();
        }
    });

    socket.on('play_again', function(orderPlayer) {
        newGameClientCleanUp(orderPlayer);
    });

    socket.on('game_over', function(gameState) {
        document.getElementById('score').innerHTML = "Score: " + gameState.score[0].toString() + "-" + gameState.score[1].toString();

        if (gameState.winner == myPlayerIndex) {
            alert("You have won!");
            newGamePopUp();
        }
        else {
            alert("You have lost :(");
        }

    });

    document.getElementById('player-0-name').innerHTML = player_0_name;

    if (myPlayerIndex == 0) {
        setPlayerLoading(1);
        document.getElementById('player-1-name').innerHTML = "Waiting for other player...";
    }

    else if (myPlayerIndex == 1) {
        setPlayerLoading(0);
        document.getElementById('player-1-name').innerHTML = player_1_name;
        //waitGameStartLoop();
    }
});

function setPlayerLoading(player_index) {
    document.getElementById('loading-div-' + player_index.toString()).innerHTML = '<img id="loading-gif" height="" src="' + loading_gif_url + '">';

    $("#loading-gif").css('height', '30px');
}

function removePlayerLoading(player_index) {
    document.getElementById('loading-div-' + player_index.toString()).innerHTML = '';
}

function reStyleCells(stylesheet){
   $('#cell-styles').attr("href",stylesheet);
}

function chooseRolePopUp() {
    removePlayerLoading(1);
    document.getElementById("chooseRole").style.display = "block";
    document.getElementById("chooseRole").style.zIndex = 15;
    overlay();
}

function roleChosen(roleIndex) {
    document.getElementById("chooseRole").style.display = "none";
    removeOverlay();

    data = jsonData();
    data.roleChosen = roleIndex;

    socket.emit('role_chosen', data);
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
    $('#' + elt.id).removeClass('game-tile-0').addClass('game-tile-' + color.toString());
    reStyleCells(cellStyle_url + '?v=' + new Date().getTime());
    
    data = jsonData();
    data.cell = elt.id;
    data.color = color.toString();
    socket.emit('turn_played', data);
}

function newGamePopUp() {
    document.getElementById("newGame").style.display = "block";
    document.getElementById("newGame").style.zIndex = 15;
    overlay();
}

function newGame(playagain) {
    document.getElementById("newGame").style.display = "none";
    removeOverlay();

    data = jsonData();
    data.newGameBool = playagain;

    socket.emit('play_again', data);

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

    data = jsonData();

    socket.emit('surrender', data);
} 