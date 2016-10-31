from ..dependencies import tk
from ..game import Reversi, Player
from .utils import Animator
from .main_menu_ctl import MainMenuController
from .game_ctl import GameController


class ReversiApp(object):

    # common parameters
    CELL_SIZE = 50
    GAME_FIELD_SIZE = CELL_SIZE * Reversi.FIELD_SIZE
    PADDING = 5
    TOP_PANEL_HEIGHT = CELL_SIZE
    BACKGROUND = '#532'

    def __init__(self, tk_root):
        self._controller = None

        self._setup_window(tk_root)
        self._tk_root = tk_root
        self.delay_apply = tk_root.after
        self._run_animation = Animator(
            check_closed=lambda: getattr(self, '_was_closed'),
            delay_apply=self.delay_apply
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
        tk_root.wm_title('TkReversi')
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

    def get_app_window(self):
        return self._tk_root

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

    def update_game_scores(self, black_cnt, white_cnt):
        cnv = self._scores_canvas
        cnv_width = cnv.winfo_width()
        cnv_height = cnv.winfo_height()

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

    def start_game(self, black_ai, white_ai):
        self._setup_controller(
            GameController,
            black_ai=black_ai,
            white_ai=white_ai,
        )
