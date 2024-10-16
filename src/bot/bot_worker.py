from PyQt6.QtCore import QThread, pyqtSignal
from src.bot.bot_helper import get_intelligent_moves, minimax
import time

from src.helpers.valid_moves_helper import get_valid_moves_helper

last_two_moves = []

class BotWorker(QThread):
    move_computed = pyqtSignal(str, tuple)

    def __init__(self, game_state, player, blocked_roads, search_depth, available_walls, difficulty, parent=None):
        super().__init__(parent)
        self.game_state = game_state
        self.difficulty = difficulty
        self.player = player
        self.blocked_roads = blocked_roads
        self.search_depth = search_depth
        self.available_walls = available_walls
        self.best_move = None
        self._is_running = True

    def run(self):
        global last_two_moves
        start_time = time.time()

        best_move = None
        best_type= None
        best_move_sequence = []
        best_value = float('-inf')
        maximizing_player_color = self.player.color
        opponent_color = self.game_state.get_opponent_color(maximizing_player_color)
        opponent_player = self.game_state.get_player_by_color(opponent_color)

        ordered_moves = self.moves_on_difficulty()
        if not ordered_moves:
            valid_moves = get_valid_moves_helper(self.player, opponent_player, self.player.grid_size, self.blocked_roads)
            ordered_moves= list(valid_moves.items())

        alpha = float('-inf')
        beta = float('inf')

        #region MINIMAX ALGORITHM

        for type, move in ordered_moves:
            if not self._is_running:  # Check if the thread should stop
                print("Bot worker stopped.")
                last_two_moves = []
                return  # Exit the run method safely

            game_state_copy = self.game_state.simulate_move_or_wall(type, move, self.player)
            nodes_examined = {'count': 0}

            move_value, move_sequence = minimax(
                game_state_copy,
                self.search_depth - 1,
                alpha,
                beta,
                maximizing_player_color,
                opponent_color,
                nodes_examined,
                difficulty=self.difficulty,
                move_sequence=[],
            )

            # If the bot has no walls left, go for the shortest path
            if self.available_walls == 0:
                if move_value > -1000:
                    best_move = move
                    best_type = type
                    best_value = move_value
                    break

            # Check if the bot is stuck (repeating the same move)
            if len(last_two_moves) > 0 and last_two_moves[-1] == (type, move):
                move_value -= 5  # Penalize the repeated move

            if move_value > best_value:
                best_value = move_value
                best_type = type
                best_move = move
                best_move_sequence = move_sequence
                alpha = max(alpha, move_value)

            if beta <= alpha:
                break
        #endregion

        if best_move:
            print(f"Evaluation: {best_value:.2f}")
            print("Best move sequence:", best_type, best_move, best_move_sequence)
            self.best_type = best_type
            self.best_move = best_move

        # Convert best_move to tuple if it's a list (mainly for wall moves)
        if isinstance(best_move, list):
            best_move = tuple(best_move)

        # End the timer and calculate elapsed time
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Bot thought for {elapsed_time:.2f} seconds.")

        last_two_moves.append((best_type, best_move))
        last_two_moves = last_two_moves[-2:]  # Keep only the last 2 moves

        # Force moves if the bot is stuck
        if not best_move:
            if not ordered_moves and self.available_walls == 0:
                self.move_computed.emit('skip', ())
            else:
                best_type, best_move = ordered_moves[0]
                self.move_computed.emit(best_type, best_move)
        else:
            self.move_computed.emit(best_type, best_move)

    def moves_on_difficulty(self):
        intelligent_moves, other_moves = get_intelligent_moves(self.game_state, self.player, self.player.grid_size,
                                                               self.blocked_roads, self.available_walls)
        if self.difficulty == 'easy':
            return intelligent_moves
        else:
            return intelligent_moves + other_moves

    def stop(self):
        """Stop the thread gracefully by setting the running flag to False."""
        global last_two_moves
        last_two_moves = []
        self._is_running = False