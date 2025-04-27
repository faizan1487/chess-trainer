// Global utilities and functions for the Chess Trainer application

// Function to show a toast notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `toast align-items-center text-white bg-${type} border-0`;
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', 'assertive');
    notification.setAttribute('aria-atomic', 'true');
    
    // Create inner HTML
    notification.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add to document
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.appendChild(notification);
    document.body.appendChild(container);
    
    // Initialize and show the toast
    const toast = new bootstrap.Toast(notification, {
        autohide: true,
        delay: 5000
    });
    toast.show();
    
    // Remove from DOM after hiding
    notification.addEventListener('hidden.bs.toast', function () {
        document.body.removeChild(container);
    });
}

// Function to format evaluation score
function formatEvalScore(score) {
    if (score === null || score === undefined) return 'N/A';
    
    let formattedScore;
    if (score > 0) {
        formattedScore = `+${score.toFixed(2)}`;
    } else {
        formattedScore = score.toFixed(2);
    }
    
    return formattedScore;
}

// Function to convert FEN to a readable position description
function describeFEN(fen) {
    if (!fen) return '';
    
    const parts = fen.split(' ');
    const turn = parts[1] === 'w' ? 'White' : 'Black';
    
    return `${turn} to move`;
}

// Function to highlight elements
function highlight(element, duration = 2000) {
    if (!element) return;
    
    element.classList.add('highlight-animation');
    setTimeout(() => {
        element.classList.remove('highlight-animation');
    }, duration);
}

// Add CSRF token to all AJAX requests
function setupAjaxCSRF() {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');
    
    // Set up AJAX requests to include CSRF token
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
}

// Initialize when document is ready
$(document).ready(function() {
    // Setup CSRF token for AJAX
    setupAjaxCSRF();
    
    // Initialize any tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Initialize any popovers
    $('[data-bs-toggle="popover"]').popover();
    
    // Add a class to the active navigation link
    const currentPage = window.location.pathname;
    $('.navbar-nav .nav-link').each(function() {
        const href = $(this).attr('href');
        if (href === currentPage) {
            $(this).addClass('active');
        }
    });
});

// Common initialization code for chess board
document.addEventListener('DOMContentLoaded', function() {
    // Initialize chessboard on the game page
    const gameBoard = document.getElementById('game-board');
    if (gameBoard) {
        // Default board configuration
        const config = {
            position: 'start',
            draggable: true,
            pieceTheme: '/static/chess_app/img/chesspieces/wikipedia/{piece}.png'
        };
        
        // Initialize the board
        const board = Chessboard('game-board', config);
        
        // Handle board flipping
        const flipButton = document.getElementById('flip-board');
        if (flipButton) {
            flipButton.addEventListener('click', function() {
                board.flip();
            });
        }
        
        // Handle board resizing
        window.addEventListener('resize', function() {
            board.resize();
        });
    }
    
    // Initialize chessboard on the challenge detail page
    const challengeBoard = document.getElementById('challenge-board');
    if (challengeBoard) {
        // Get FEN from data attribute if available
        const fen = challengeBoard.getAttribute('data-fen') || 'start';
        
        // Challenge board configuration
        const config = {
            position: fen,
            draggable: true,
            pieceTheme: '/static/chess_app/img/chesspieces/wikipedia/{piece}.png'
        };
        
        // Initialize the board
        const board = Chessboard('challenge-board', config);
        
        // Handle board flipping
        const flipButton = document.getElementById('flip-board');
        if (flipButton) {
            flipButton.addEventListener('click', function() {
                board.flip();
            });
        }
        
        // Handle board resizing
        window.addEventListener('resize', function() {
            board.resize();
        });
    }
}); 