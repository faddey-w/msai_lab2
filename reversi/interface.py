import tkinter as tk
import time
from tkinter import messagebox
from .game import Reversi, GameEvent, Player


class ReversiApp:

    # common parameters
    CELL_SIZE = 50
    GAME_FIELD_SIZE = CELL_SIZE * Reversi.FIELD_SIZE
    PADDING = 5
    TOP_PANEL_HEIGHT = CELL_SIZE
    BACKGROUND = '#532'

    def __init__(self, tk_root: tk.Tk):
        self._controller = None

        self._setup_window(tk_root)
        self._tk_root = tk_root
        self._run_animation = Animator(
            check_closed=lambda: getattr(self, '_was_closed'),
            delay_apply=tk_root.after
        )

        def on_close():
            self._was_closed = True
            self._tk_root.destroy()
        self._was_closed = False
        tk_root.protocol("WM_DELETE_WINDOW", on_close)

        root_frame = tk.Frame(tk_root, background=self.BACKGROUND)
        root_frame.pack(expand=1, fill=tk.BOTH)

        top_panel = self._init_top_panel(root_frame)
        self._status_label = self._init_status_label(top_panel)
        self._scores_canvas = self._init_scores_canvas(top_panel)
        self._field_canvas = self._init_field_canvas(root_frame)
        tk_root.after_idle(self.go_to_main_menu)

    def _setup_window(self, tk_root):
        wnd_width = self.GAME_FIELD_SIZE + 2*self.PADDING
        wnd_height = self.GAME_FIELD_SIZE + self.TOP_PANEL_HEIGHT + 3*self.PADDING
        scr_width = tk_root.winfo_screenwidth()
        scr_height = tk_root.winfo_screenheight()
        x = (scr_width - wnd_width) // 2
        y = (scr_height - wnd_height) // 2
        tk_root.geometry(
            '{}x{}+{}+{}'.format(wnd_width, wnd_height, x, y)
        )
        tk_root.resizable(width=False, height=False)

    def _init_top_panel(self, parent_frame):
        top_frame = tk.Frame(parent_frame, background=self.BACKGROUND)
        top_frame.place(
            x=self.PADDING, y=self.PADDING,
            width=self.GAME_FIELD_SIZE, height=self.TOP_PANEL_HEIGHT,
        )
        return top_frame

    def _init_status_label(self, parent_frame):
        status_label = tk.Label(
            parent_frame, background=self.BACKGROUND,
            foreground='#FFF'
        )
        status_label.pack(side=tk.LEFT)
        return status_label

    def _init_scores_canvas(self, parent_frame):
        scores_canvas = tk.Canvas(
            parent_frame,
            relief=tk.FLAT,
            highlightthickness=0,
        )
        scores_canvas.place(
            relwidth=0.25, relheight=1, relx=0.75, rely=0
        )

        def on_click(event):
            if hasattr(self._controller, 'on_score_view_click'):
                self._controller.on_score_view_click()
        scores_canvas.bind('<Button-1>', on_click)

        return scores_canvas

    def _init_field_canvas(self, parent_frame):
        field_canvas = tk.Canvas(
            parent_frame,
            highlightthickness=0,
            relief=tk.GROOVE,
        )
        field_canvas.place(
            x=self.PADDING, y=self.TOP_PANEL_HEIGHT + 2*self.PADDING,
            width=self.GAME_FIELD_SIZE, height=self.GAME_FIELD_SIZE)

        def on_click(event):
            if hasattr(self._controller, 'on_field_click'):
                row_id = event.x // self.CELL_SIZE
                col_id = event.y // self.CELL_SIZE
                self._controller.on_field_click(row_id, col_id)
        field_canvas.bind('<Button-1>', on_click)

        return field_canvas

    def _setup_controller(self, controller_cls, **kwargs):
        self._controller = controller_cls(self, **kwargs)
        if hasattr(self._controller, 'initialize'):
            self._controller.initialize()

    def go_to_main_menu(self):
        self._setup_controller(MainMenuController)

    def set_status(self, message):
        self._status_label.configure(text=message)

    def display_play_prompt(self):
        cnv = self._scores_canvas
        cnv_width = cnv.winfo_width()
        cnv_height = cnv.winfo_height()
        cnv.create_rectangle(
            0, 0, cnv_width, cnv_height,
            outline='#000', fill='#FFF', width=5
        )
        cnv.create_text(
            cnv_width//2, cnv_height//2,
            text='Play', fill='#000'
        )

    def update_game_scores(self):
        game = self._controller.game
        cnv = self._scores_canvas
        cnv_width = cnv.winfo_width()
        cnv_height = cnv.winfo_height()
        white_cnt, black_cnt = game.get_scores()

        cnv.create_rectangle(
            0, 0, cnv_width // 2, cnv_height, fill='#000')
        cnv.create_text(
            cnv_width // 4, cnv_height // 2,
            text=str(black_cnt), fill='#FFF')

        cnv.create_rectangle(
            cnv_width//2, 0, cnv_width, cnv_height, fill='#FFF')
        cnv.create_text(
            3 * cnv_width // 4, cnv_height // 2,
            text=str(white_cnt), fill='#000')

    def draw_field_background(self):
        background = '#262'
        delim_color = '#880'

        cnv = self._field_canvas
        width = cnv.winfo_width()
        height = cnv.winfo_height()
        cnv.create_rectangle(
            0, 0, width, height, fill=background,
            outline=delim_color, width=6
        )

        for step in range(1, Reversi.FIELD_SIZE):
            offset = step * self.CELL_SIZE
            cnv.create_line(0, offset, self.GAME_FIELD_SIZE, offset,
                            fill=delim_color, width=1)
            cnv.create_line(offset, 0, offset, self.GAME_FIELD_SIZE,
                            fill=delim_color, width=1)

    def show_appear(self, row_id, col_id, player, callback=None):
        center_x = row_id * self.CELL_SIZE + self.CELL_SIZE // 2
        center_y = col_id * self.CELL_SIZE + self.CELL_SIZE // 2
        color = '#FFF' if player == Player.White else '#000'

        def redraw_cell(cell_size):
            cell_size = int(cell_size)
            self._field_canvas.create_oval(
                center_x-cell_size, center_y-cell_size,
                center_x+cell_size, center_y+cell_size,
                fill=color
            )
        self._run_animation(
            redraw_cell,
            0, self.CELL_SIZE//2 - self.PADDING,
            400, callback
        )

    def show_change_owner(self, row_id, col_id, player, callback=None):
        center_x = row_id * self.CELL_SIZE + self.CELL_SIZE // 2
        center_y = col_id * self.CELL_SIZE + self.CELL_SIZE // 2
        color = '#FFF' if player == Player.White else '#000'
        opponent_color = '#000' if player == Player.White else '#FFF'
        full_cell_size = self.CELL_SIZE//2 - self.PADDING

        def redraw_cell(cell_size):
            cell_size = int(cell_size)
            self._field_canvas.create_oval(
                center_x-full_cell_size, center_y-full_cell_size,
                center_x+full_cell_size, center_y+full_cell_size,
                fill=color
            )
            if cell_size > 0:
                self._field_canvas.create_oval(
                    center_x-cell_size, center_y-cell_size,
                    center_x+cell_size, center_y+cell_size,
                    fill=opponent_color
                )
        self._run_animation(
            redraw_cell,
            full_cell_size, 0,
            400, callback
        )

    def start_game(self):
        self._setup_controller(UserVsUserController)


class Animator:

    FRAMES_PER_SECOND = 15

    def __init__(self, check_closed, delay_apply):
        self._is_closed = check_closed
        self._delay_apply = delay_apply
        self._entries = []
        self._worker_id = None
        # it seems that Tk.after() accepts only raw functions, not methods
        self._worker_caller = lambda: self._worker()

    def __call__(self, function, start_val, stop_val, duration, callback=None):
        if self._worker_id is None:
            self._schedule_worker()
        self._entries.append(self._Entry(
            function, start_val, stop_val,
            duration, callback
        ))

    def _worker(self):
        # check if we should stop
        if self._is_closed() or not self._entries:
            self._worker_id = None
            return
        # here we provide the safe way to add new animations
        # from within callbacks or step functions
        remove_indices = set()
        entry_dict = dict(enumerate(self._entries))
        self._entries.clear()

        # perform all animation steps within single event of event-loop
        # that's why this class was created:
        # all animations will be rendered to the display at once
        # instead of touching the slow display after each step
        for idx, entry in entry_dict.items():
            ts = time.time() * 1000
            ratio = (ts - entry.start_ts) / entry.duration
            start, stop = entry.start_val, entry.stop_val
            if ratio <= 1:
                entry.function(start + ratio * (stop-start))
            else:
                entry.function(stop)
                remove_indices.add(idx)
                if entry.callback:
                    entry.callback()
        # remove finished animations
        for idx in remove_indices:
            entry_dict.pop(idx)
        # put pending animations into the list again
        # note that self._entries may be not empty at that point
        self._entries.extend(entry_dict.values())

        #
        self._schedule_worker()

    class _Entry:
        def __init__(self, function, start_val, stop_val, duration, callback):
            self.function = function
            self.start_val = start_val
            self.stop_val = stop_val
            self.duration = duration
            self.callback = callback
            self.start_ts = time.time() * 1000

    def _schedule_worker(self):
        period = 1000 // self.FRAMES_PER_SECOND
        w_id = self._delay_apply(period, self._worker_caller)
        self._worker_id = w_id


class MainMenuController:

    def __init__(self, app: ReversiApp):
        self.app = app
        self.app.display_play_prompt()
        self.app.draw_field_background()

    def on_score_view_click(self):
        self.app.start_game()
        # messagebox.showerror(
        #     "Turning you down",
        #     "Wanna to play? Implement the game before!"
        # )


class UserVsUserController:

    def __init__(self, app: ReversiApp):
        self.app = app
        self.game = Reversi.New(
            on_cant_move=self._on_cant_move,
            on_game_over=self._on_game_over,
            on_cell_change=self._on_cell_change,
            on_normal_turn=self._on_normal_turn,
        )
        self._react_on_click = False

    def initialize(self):
        self.app.draw_field_background()
        for (row_id, col_id), cell in self.game.iter_cells():
            if cell is not None:
                self.app.show_appear(
                    row_id, col_id, cell,
                    callback=self._on_animation_end
                )
        self.app.set_status("{} player's turn"
                            .format(self.game.current_player.name))
        self.app.update_game_scores()

    def on_field_click(self, row_id, col_id):
        if not self._react_on_click:
            return
        if self.game.is_game_over:
            self.app.go_to_main_menu()
            return
        if (row_id, col_id) not in self.game.get_possible_turns():
            return
        self.game.make_turn(row_id, col_id)

    def _on_animation_end(self):
        self._react_on_click = True

    def _on_cell_change(self, row_id, col_id, new_player, prev_player):
        if prev_player is None:
            method = self.app.show_appear
        else:
            method = self.app.show_change_owner
        self._react_on_click = False
        method(row_id, col_id, new_player, callback=self._on_animation_end)

    def _on_cant_move(self, player):
        self.app.update_game_scores()
        self.app.set_status(
            "{} player can not move. {} moves again."
            .format(player.name, player.opposite.name)
        )

    def _on_normal_turn(self, next_player):
        self.app.update_game_scores()
        self.app.set_status("{} player's turn"
                            .format(next_player.name))

    def _on_game_over(self):
        winner = self.game.get_winner()
        self.app.update_game_scores()
        self.app.set_status("{} player wins!".format(winner.name))


def main():
    root = tk.Tk()

    _platform_specific_init()

    ReversiApp(root)
    root.mainloop()


def _platform_specific_init():
    from os import system, getenv
    from platform import system as platform
    if platform() == 'Darwin':
        if getenv('REVERSI_DEVEL', ''):
            # focus on Tk window, development only
            # in production we'll build the application with py2app
            system('''/usr/bin/osascript -e '''
                   ''' 'tell app "Finder" to set frontmost '''
                   '''  of process "Python" to true' ''')
