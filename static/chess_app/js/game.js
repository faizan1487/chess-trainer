// Ensure move data is correctly formatted and sent

function sendMove(moveUCI, positionBefore, positionAfter) {
    const moveData = {
        move_uci: moveUCI,
        position_before: positionBefore,
        position_after: positionAfter
    };

    $.ajax({
        url: `/game/${gameId}/move/`,
        type: 'POST',
        data: moveData,
        success: function(data) {
            // Display move feedback
            displayFeedback(data);
            
            // Update move history
            updateMoveHistory();

            // Request AI move if game not over
            if (!game.game_over()) {
                setTimeout(getAIMove, 1000);
            }
        },
        error: function(error) {
            console.error("Error sending move:", error);
            $('#feedback-container').html('<div class="alert alert-danger">Error analyzing move. Please try again.</div>');
        }
    });
} 