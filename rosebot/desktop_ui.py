import tkinter as tk

from rosebot import domain as d
from rosebot import search

CELL = 96
MARGIN = 28
PAD = 16

COLOR_HEX = {
    "red": "#e23b3b", "pink": "#ff8fb3", "white": "#e9e9ef", "crimson": "#8e1d2d",
    "yellow": "#e6c200", "violet": "#8a5cd1", "orange": "#f08a2e", "green": "#3fa34d",
    "mauve": "#b784a7", "purple": "#7d3cc1", "gold": "#d4af37", "lightpink": "#ffc6d9",
}
TYPE_HEX = {"Rose": "#e23b3b", "Tulip": "#7d3cc1", "Orchid": "#9b59b6", "Goliat": "#caa030"}

BG = "#0f1426"
CELL_BG = "#1c2440"
WH_BG = "#2a2438"
GRID_LINE = "#2a335a"
FG = "#e8ecf6"
MUTED = "#9aa3c0"


def _solve():
    engine = search.run_astar()
    goal = search.solution_node(engine)
    if goal is None:
        return None, None
    return search.reconstruct_states(engine, goal["nid"]), goal["g"]


class RoseBotApp(tk.Tk):
    def __init__(self, states, total_cost):
        super().__init__()
        self.title(f"RoseBot — {d.LEVEL_NAME}")
        self.configure(bg=BG)
        self.states = states
        self.total_cost = total_cost
        self.i = 0
        self.playing = False
        self._job = None

        board_w = MARGIN * 2 + d.GRID_W * CELL
        board_h = MARGIN * 2 + d.GRID_H * CELL

        root = tk.Frame(self, bg=BG)
        root.pack(padx=PAD, pady=PAD)

        self.canvas = tk.Canvas(root, width=board_w, height=board_h,
                                bg=BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0, rowspan=2, sticky="n")

        self.panel = tk.Frame(root, bg=BG)
        self.panel.grid(row=0, column=1, sticky="n", padx=(PAD, 0))

        self._pav_text = {}   # pid -> canvas text id
        self._build_board()
        self._build_panel()
        self.render(0)

    # ---- drawing -------------------------------------------------------- #
    def _cell_origin(self, y, x):
        return MARGIN + (x - 1) * CELL, MARGIN + (y - 1) * CELL

    def _build_board(self):
        c = self.canvas
        for y in range(1, d.GRID_H + 1):
            for x in range(1, d.GRID_W + 1):
                x0, y0 = self._cell_origin(y, x)
                is_wh = (y, x) == tuple(d.WAREHOUSE)
                c.create_rectangle(x0, y0, x0 + CELL, y0 + CELL,
                                   fill=WH_BG if is_wh else CELL_BG,
                                   outline=GRID_LINE, width=1)
                c.create_text(x0 + CELL - 6, y0 + 6, anchor="ne",
                              text=f"Y{y} X{x}", fill="#5a648c", font=("TkDefaultFont", 7))
        # warehouse label
        wx0, wy0 = self._cell_origin(*d.WAREHOUSE)
        c.create_text(wx0 + CELL / 2, wy0 + 16, text="W · Warehouse", fill="#d8c5ff",
                      font=("TkDefaultFont", 10, "bold"))
        # pavilions
        for p in d.PAVILIONS:
            x0, y0 = self._cell_origin(*p.pos)
            c.create_rectangle(x0 + 3, y0 + 3, x0 + CELL - 3, y0 + CELL - 3,
                               outline=TYPE_HEX.get(p.ftype, "#888"), width=2)
            c.create_text(x0 + CELL / 2, y0 + 16, text=f"{p.pid} · {p.ftype}",
                          fill=TYPE_HEX.get(p.ftype, FG), font=("TkDefaultFont", 9, "bold"))
            self._pav_text[p.pid] = c.create_text(
                x0 + CELL / 2, y0 + 52, text="", fill=FG,
                font=("TkDefaultFont", 8), width=CELL - 12, justify="center")
        # robot
        r = CELL * 0.30
        self._robot = c.create_oval(0, 0, 2 * r, 2 * r, fill="#2f7fd6",
                                    outline="#bfe4ff", width=2)
        self._robot_txt = c.create_text(0, 0, text="R", fill="#ffffff",
                                        font=("TkDefaultFont", 16, "bold"))

    def _build_panel(self):
        tk.Label(self.panel, text="RoseBot", bg=BG, fg=FG,
                 font=("TkDefaultFont", 16, "bold")).pack(anchor="w")
        tk.Label(self.panel, text=f"Optimal A* plan — total cost {self.total_cost}",
                 bg=BG, fg=MUTED).pack(anchor="w", pady=(0, 10))

        ctrl = tk.Frame(self.panel, bg=BG)
        ctrl.pack(anchor="w", pady=4)
        tk.Button(ctrl, text="⏮ Prev", command=self.prev).pack(side="left")
        self.play_btn = tk.Button(ctrl, text="▶ Play", command=self.toggle)
        self.play_btn.pack(side="left", padx=6)
        tk.Button(ctrl, text="Next ⏭", command=self.next).pack(side="left")

        self.slider = tk.Scale(self.panel, from_=0, to=len(self.states) - 1,
                               orient="horizontal", command=self._on_slide,
                               bg=BG, fg=FG, highlightthickness=0, length=280,
                               troughcolor=CELL_BG)
        self.slider.pack(anchor="w", pady=6)

        self.step_lbl = tk.Label(self.panel, bg=BG, fg=FG, font=("TkDefaultFont", 11))
        self.step_lbl.pack(anchor="w")
        self.op_lbl = tk.Label(self.panel, bg=BG, fg="#9fe0a0",
                               font=("TkDefaultFont", 10), wraplength=300, justify="left")
        self.op_lbl.pack(anchor="w", pady=(2, 10))

        tk.Label(self.panel, text="Robot is carrying:", bg=BG, fg=MUTED).pack(anchor="w")
        self.load_lbl = tk.Label(self.panel, bg=BG, fg=FG, wraplength=300,
                                 justify="left", font=("TkDefaultFont", 10))
        self.load_lbl.pack(anchor="w", pady=(0, 10))

        self.goal_lbl = tk.Label(self.panel, text="Pavilion needs remaining:",
                                 bg=BG, fg=MUTED)
        self.goal_lbl.pack(anchor="w")
        self.pav_lbls = {}
        for p in d.PAVILIONS:
            lbl = tk.Label(self.panel, bg=BG, fg=FG, anchor="w",
                           font=("TkDefaultFont", 10))
            lbl.pack(anchor="w", fill="x")
            self.pav_lbls[p.pid] = lbl

    # ---- state -> view -------------------------------------------------- #
    @staticmethod
    def _needs_map(step):
        m = {}
        for pid, color, n in step["needs"]:
            m.setdefault(pid, {})[color] = n
        return m

    def render(self, i):
        step = self.states[i]
        y, x = step["pos"]
        x0, y0 = self._cell_origin(y, x)
        r = CELL * 0.30
        cx, cy = x0 + CELL / 2, y0 + CELL / 2
        self.canvas.coords(self._robot, cx - r, cy - r, cx + r, cy + r)
        self.canvas.coords(self._robot_txt, cx, cy)

        nm = self._needs_map(step)
        all_done = True
        for p in d.PAVILIONS:
            rem = nm.get(p.pid, {})
            lines = []
            for color, base in sorted(p.needs.items()):
                left = rem.get(color, 0)
                if left > 0:
                    all_done = False
                lines.append(f"{color} {base - left}/{base}")
            self.canvas.itemconfig(self._pav_text[p.pid], text="\n".join(lines))
            total = sum(rem.values())
            mark = "✓ done" if total == 0 else f"{total} left"
            self.pav_lbls[p.pid].config(
                text=f"  {p.pid} · {p.ftype} (Y{p.pos[0]} X{p.pos[1]}): {mark}",
                fg="#9fe0a0" if total == 0 else FG)

        load = step["load"]
        self.load_lbl.config(
            text="— empty —" if not load
            else "   ".join(f"{t} {c} ×{n}" for t, c, n in load))

        self.step_lbl.config(text=f"Step {i} / {len(self.states) - 1}    "
                                  f"cost g = {step['g']}")
        self.op_lbl.config(text=f"op: {step['op']}")
        self.goal_lbl.config(
            text=("GOAL — all pavilions satisfied, robot empty!"
                  if all_done else "Pavilion needs remaining:"))
        if self.slider.get() != i:
            self.slider.set(i)
        self.i = i

    # ---- controls ------------------------------------------------------- #
    def _go(self, i):
        self.render(max(0, min(len(self.states) - 1, i)))

    def _on_slide(self, val):
        if int(val) != self.i:
            self.stop()
            self._go(int(val))

    def prev(self):
        self.stop()
        self._go(self.i - 1)

    def next(self):
        self.stop()
        self._go(self.i + 1)

    def stop(self):
        self.playing = False
        self.play_btn.config(text="▶ Play")
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None

    def toggle(self):
        if self.playing:
            self.stop()
            return
        self.playing = True
        self.play_btn.config(text="⏸ Pause")
        if self.i >= len(self.states) - 1:
            self._go(0)
        self._tick()

    def _tick(self):
        if not self.playing:
            return
        if self.i >= len(self.states) - 1:
            self.stop()
            return
        self._go(self.i + 1)
        self._job = self.after(650, self._tick)


def launch():
    """Solve, then open the desktop window (blocks until closed)."""
    states, cost = _solve()
    if states is None:
        print("No solution to visualize.")
        return 1
    app = RoseBotApp(states, cost)
    app.mainloop()
    return 0
