import time
import threading
from ..game import Reversi, Player
from .utils import CallbackJoiner


class GameController:

    def __init__(self, app, black_ai, white_ai):
        self.app = app
        """@type: reversi.interface.ReversiApp"""

        self.game = Reversi.New(
            on_cant_move=self._on_cant_move,
            on_game_over=self._on_game_over,
            on_cell_change=self._on_cell_change,
            on_normal_move=self._on_normal_move,
        )
        self._ai = {
            Player.Black: black_ai,
            Player.White: white_ai,
        }
        self._react_on_click = False
        self._joiner = CallbackJoiner(self._on_animation_end)
        self._ai_thread = None
        self._ai_move = None
        self._check_ai_done = lambda: self._check_ai_done_impl()

    def initialize(self):
        self.app.draw_field_background()
        for (row_id, col_id), cell in self.game.iter_cells():
            if cell is not None:
                # we run animations
                # first move will begin when these animations will end
                # see `_on_animation_end`
                self.app.show_appear(
                    row_id, col_id, cell,
                    callback=self._joiner.make_callback()
                )
        self.app.update_game_scores(*self.game.get_scores())
        self.app.set_status("{} player's move"
                            .format(self.game.current_player.name))

    def on_field_click(self, row_id, col_id):
        if not self._react_on_click:
            return
        if self.game.is_game_over:
            self.app.go_to_main_menu()
            return
        if (row_id, col_id) not in self.game.get_possible_moves():
            return
        self.game.make_move(row_id, col_id)

    def _on_animation_end(self):
        # animation is the final stage of every move
        # game's current_player already changed to the next player
        # so...
        if self.game.is_game_over:
            return
        self._begin_move(self.game.current_player)

    def _on_cell_change(self, row_id, col_id, new_player, prev_player):
        if prev_player is None:
            method = self.app.show_appear
        else:
            method = self.app.show_change_owner
        self._react_on_click = False
        method(row_id, col_id, new_player,
               callback=self._joiner.make_callback())

    def _on_cant_move(self, player):
        self.app.update_game_scores(*self.game.get_scores())
        self.app.set_status(
            "{} player can not move. {} moves again."
            .format(player.name, player.opponent.name)
        )

    def _on_normal_move(self, next_player):
        self.app.update_game_scores(*self.game.get_scores())
        self.app.set_status("{} player's move"
                            .format(next_player.name))

    def _on_game_over(self):
        self._ai_thread = None
        self._react_on_click = True
        winner = self.game.get_winner()
        self.app.update_game_scores(*self.game.get_scores())
        if winner:
            self.app.set_status("{} player wins!".format(winner.name))
        else:
            self.app.set_status("Draw!")

    def _begin_move(self, player):
        ai = self._ai[player]
        if ai is None:
            # enable clicking at game field and wait for user's decision
            self._react_on_click = True
        else:
            # block user actions and run AI in background
            self._react_on_click = False
            self._ai_thread = threading.Thread(target=self._ai_worker, args=[ai])
            self._ai_thread.start()
            # We should call make_move only in main thread!
            # This is due to Tkinter's poor thread-safety.
            # In practice, tk_root.after() may take 20-30 seconds
            # if called from non-main thread.
            self.app.delay_apply(5, self._check_ai_done)

    def _ai_worker(self, ai_func):
        self._ai_move = None
        time.sleep(0.5)
        self._ai_move = ai_func(self.game)

    def _check_ai_done_impl(self):
        if self._ai_thread is None:
            return
        if self._ai_thread.is_alive():
            self.app.delay_apply(5, self._check_ai_done)
            return
        self.game.make_move(*self._ai_move)
