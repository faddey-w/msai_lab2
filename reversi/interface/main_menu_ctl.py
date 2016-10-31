from ..dependencies import tk, simpledialog, enum
from .. import ai_player
from ..game import Player


class MainMenuController(object):

    def __init__(self, app):
        self.app = app
        """@type: reversi.interface.ReversiApp"""

        self.app.display_play_prompt()
        self.app.draw_field_background()

    def on_score_view_click(self):
        dialog = PlayerSetupDialog(self.app.get_app_window())
        if not dialog.is_ok:
            return
        self.app.start_game(dialog.black_ai, dialog.white_ai)


class PlayerSetupDialog(simpledialog.Dialog):

    def __init__(self, app_window):
        self.black_ai, self.white_ai, self.is_ok = None, None, False
        self.black_form, self.white_form = None, None
        simpledialog.Dialog.__init__(self, app_window, 'Game Setup')

    def body(self, frame):
        self.geometry('350x450')
        self.resizable(width=False, height=False)

        tk.Label(frame, text='Black').grid(row=0, column=0, sticky='e')
        black_form_frame = tk.Frame(frame, height=160, width=340)
        black_form_frame.grid_propagate(False)
        black_form_frame.grid(row=1, column=0, columnspan=3)
        tk.OptionMenu(
            frame, tk.StringVar(frame, AIType.Player), *AIType,
            command=self.fill_form(black_form_frame, Player.Black)
        ).grid(row=0, column=1, columnspan=2, sticky='ew')
        self.fill_form(black_form_frame, Player.Black, AIType.Player)

        tk.Label(frame, text='White').grid(row=2, column=0, sticky='e')
        white_form_frame = tk.Frame(frame, height=160, width=340)
        white_form_frame.grid_propagate(False)
        white_form_frame.grid(row=3, column=0, columnspan=3)
        tk.OptionMenu(
            frame, tk.StringVar(frame, AIType.Player), *AIType,
            command=self.fill_form(white_form_frame, Player.White)
        ).grid(row=2, column=1, columnspan=2, sticky='ew')
        self.fill_form(white_form_frame, Player.White, AIType.Player)

        return frame

    def fill_form(self, frame, player, ai_type=None, **defaults):
        if ai_type is None:
            def callback(ai_type_):
                self.fill_form(frame, player, ai_type_)
            return callback
        for widget in frame.winfo_children():
            widget.destroy()

        form_class = FORM_MAP[ai_type]
        form = form_class(frame, **defaults)
        setattr(self, player.name.lower()+'_form', form)

    def apply(self):
        self.black_ai = self.black_form.get_ai(Player.Black)
        self.white_ai = self.white_form.get_ai(Player.White)
        self.is_ok = True


class AIType(str, enum.Enum):
    Player = 'Player'
    MaterialAdv = 'Material advantage AI'
    PositionAdv = 'Position advantage AI'


class PlayerForm(object):

    def __init__(self, frame):
        pass

    def get_ai(self, player):
        return None


class DepthSelectForm(object):

    def __init__(self, frame, **defaults):
        self._use_variable_depth = tk.BooleanVar(
            frame, defaults.get('use_variable_depth', False))
        self._const_depth = tk.StringVar(
            frame, defaults.get('const_depth', 4))
        self._midgame_depth = tk.StringVar(
            frame, defaults.get('midgame_depth', 3))
        self._endgame_depth = tk.StringVar(
            frame, defaults.get('endgame_depth', 10))

        use_var_depth = self._use_variable_depth.get()

        tk.Checkbutton(
            frame, text='Use variable depth',
            variable=self._use_variable_depth,
            command=self._on_use_var_depth_changed
        ).grid(row=0, column=0, columnspan=4)

        tk.Label(frame, text='Value:').grid(row=1, column=0)
        self._const_depth_entry = ValidatedEntry(
            frame, self._const_depth, int,
            state=tk.DISABLED if use_var_depth else tk.NORMAL)
        self._const_depth_entry.grid(row=1, column=1)

        tk.Label(frame, text='Middle game:').grid(row=1, column=2)
        self._midgame_depth_entry = ValidatedEntry(
            frame, self._midgame_depth, int,
            state=tk.NORMAL if use_var_depth else tk.DISABLED)
        self._midgame_depth_entry.grid(row=1, column=3)
        tk.Label(frame, text='End game:').grid(row=2, column=2)
        self._endgame_depth_entry = ValidatedEntry(
            frame, self._endgame_depth, int,
            state=tk.NORMAL if use_var_depth else tk.DISABLED)
        self._endgame_depth_entry.grid(row=2, column=3)

    def _on_use_var_depth_changed(self):
        # print(new_value)
        if self._use_variable_depth.get():
            self._midgame_depth_entry.configure(state=tk.NORMAL)
            self._endgame_depth_entry.configure(state=tk.NORMAL)
            self._const_depth_entry.configure(state=tk.DISABLED)
        else:
            self._midgame_depth_entry.configure(state=tk.DISABLED)
            self._endgame_depth_entry.configure(state=tk.DISABLED)
            self._const_depth_entry.configure(state=tk.NORMAL)

    def get_depth(self):
        if self._use_variable_depth.get():
            return ai_player.max_depth_decision(
                middle=int(self._midgame_depth.get()),
                end=int(self._endgame_depth.get()),
            )
        else:
            return int(self._const_depth.get())


class MaterialAdvForm(DepthSelectForm):

    def __init__(self, frame, **defaults):
        super(MaterialAdvForm, self).__init__(frame, **defaults)
        self._weight_ratio = tk.StringVar(
            frame, defaults.get('weight_ratio', 1))
        tk.Label(frame, text='Weight ratio:').grid(row=4, column=1)
        ValidatedEntry(frame, self._weight_ratio, float).grid(row=4, column=2)

    def get_ai(self, player):
        return ai_player.material_advantage_ai(
            player=player,
            max_depth=self.get_depth(),
            weight_ratio=float(self._weight_ratio.get())
        )


class PositionalAdvForm(DepthSelectForm):

    def __init__(self, frame, **defaults):
        super(PositionalAdvForm, self).__init__(frame, **defaults)
        self._corner_weight = tk.StringVar(
            frame, defaults.get('corner_weight', 4))
        self._side_weight = tk.StringVar(
            frame, defaults.get('side_weight', 2))
        self._insider_ratio = tk.StringVar(
            frame, defaults.get('insider_ratio', 1))

        tk.Label(frame, text='Corner weight:').grid(row=3, column=0)
        ValidatedEntry(frame, self._corner_weight, float).grid(row=3, column=1)
        tk.Label(frame, text='Side weight:').grid(row=3, column=2)
        ValidatedEntry(frame, self._side_weight, float).grid(row=3, column=3)
        tk.Label(frame, text='Insider ratio:').grid(row=4, column=0)
        ValidatedEntry(frame, self._insider_ratio, float).grid(row=4, column=1)

    def get_ai(self, player):
        return ai_player.positional_advantage_ai(
            player=player,
            max_depth=self.get_depth(),
            corner_weight=float(self._corner_weight.get()),
            side_weight=float(self._side_weight.get()),
            insider_ratio=float(self._insider_ratio.get()),
        )


FORM_MAP = {
    AIType.Player: PlayerForm,
    AIType.MaterialAdv: MaterialAdvForm,
    AIType.PositionAdv: PositionalAdvForm,
}


def _validator(to_type):
    def validate(new_value):
        try:
            to_type(new_value)
            return True
        except:
            return False
    return validate


def ValidatedEntry(frame, variable, var_type, **kwargs):
    vcmd = (frame.register(_validator(var_type)), '%P')
    return tk.Entry(frame, textvariable=variable,
                    vcmd=vcmd, validate='key',
                    width=5, **kwargs)
