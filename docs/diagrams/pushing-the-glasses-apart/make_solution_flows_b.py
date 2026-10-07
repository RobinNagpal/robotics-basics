"""The flow charts for solutions 4, 5 and 6: what each one actually does.

Each of the three solutions has a chapter opening with a "what it is" document,
and the same pictures are shown again in that solution's short page in the
six-solutions chapter. So each picture has to carry the whole chain on its own,
for a reader who has not read the prose beside it.

    worldmodel-flow-what-it-does.png        solution 4 end to end: the pushes
                                            collected, the five copies fitted,
                                            and the search run before every
                                            push the arm makes.
    worldmodel-flow-the-five-copies.png     why there are five copies rather
                                            than one, how their disagreement is
                                            used, and the case where all five
                                            agree and are wrong together.
    smolvla-flow-what-it-does.png           solution 5, which is the shortest
                                            chain in the book: picture and words
                                            in, waypoints out, look again.
    smolvla-finetuned-flow-what-it-does.png solution 6, the same chain with a
                                            training step put in front of it.
    smolvla-finetuned-flow-the-correction.png  what low-rank adaptation is, what
                                            it costs to train and what it costs
                                            to run.

Every number written on these pictures comes out of
``code/src/09_pushing-the-glasses-apart/``, never out of the prose:

* the two rounds of collection, the five copies and the training time from
  ``04-a-world-model/README.md``; the input and output widths from
  ``04-a-world-model/features.py`` by way of the same README;
* ``ENSEMBLE = 5`` from ``04-a-world-model/model.py``, and ``TOPPLE_LIMIT``,
  ``JITTERS``, ``DRAWS``, ``ELITES`` and ``ROUNDS`` from
  ``04-a-world-model/plan.py``;
* the toppling the model rated safe from ``04-a-world-model/README.md``;
* the picture's size and height from ``bench/top_view.py``, and the instruction
  from ``05-smolvla-as-it-downloads/joining.py``;
* the demonstration counts, the moving and total parameter counts, the measured
  memory and the committed step count from
  ``06-smolvla-fine-tuned/README.md`` and
  ``06-smolvla-fine-tuned/correction/training.json``.

Run from code/:

    pixi run python ../docs/diagrams/pushing-the-glasses-apart/make_solution_flows_b.py
"""

from __future__ import annotations

import matplotlib.colors as mcolors
from diagram_style import (
    GLASS,
    GOOD,
    INK,
    LABEL_SIZE,
    MUTED,
    NOTE_SIZE,
    PAPER,
    TITLE_SIZE,
    WARN,
    bare,
    new,
    save,
)
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

# ------------------------------------------------------------------ the numbers
#
# Read out of the code and out of the folders' own result files. The comment
# after each one says where it came from, so a reader can check it in one step.

# 04-a-world-model/README.md, "Training data" and "What it costs".
ROUND_ONE_PUSHES = "24,759"
ROUND_ONE_TABLES = "4,000"
ROUND_TWO_PUSHES = "13,253"
ROUND_TWO_TABLES = "5,000"
ALL_PUSHES = "38,012"
TRAIN_MINUTES = 31
INPUTS = 34                 # features.INPUTS, quoted in that README
OUTPUTS = 14                # features.OUTPUTS, quoted in the same place
TUNING_TABLES = 100         # the tuning tables one glass went over on
TUNING_TOPPLED = 1

# 04-a-world-model/model.py and plan.py.
COPIES = 5                  # model.ENSEMBLE
TOPPLE_LIMIT = "1%"         # plan.TOPPLE_LIMIT = 0.01
JITTERS = 4                 # plan.JITTERS
FIRST_DRAWS = 600           # plan: 2 * DRAWS on the first round
LATER_DRAWS = 300           # plan.DRAWS
ROUNDS = 4                  # plan.ROUNDS
ELITES = 30                 # plan.ELITES
CANDIDATES = "1,500"        # 600 + 3 x 300, as that README puts it

# bench/top_view.py, and 05-smolvla-as-it-downloads/joining.py.
VIEW_PIXELS = "384 by 384"
VIEW_HEIGHT_MM = 750
INSTRUCTION = "the glasses are too close together, push them apart"

# 05-smolvla-as-it-downloads/README.md, and correction/training.json.
SMOLVLA_PARAMETERS = "453,859,552"
CHUNK_WAYPOINTS = 50        # the number of actions SmolVLA emits in one pass

# 06-smolvla-fine-tuned/README.md, "The demonstrations".
TRAINING_TABLES = 800
COLLECT_MINUTES = 22
DEMONSTRATIONS = "2,012"
DEMONSTRATION_TABLES = 740
REAL_PUSHES = "2,021"
DISCARDED = 9
DISCARDED_TOPPLED = 8
DISCARDED_OUT_OF_ZONE = 1

# 06-smolvla-fine-tuned/correction/training.json.
MOVING_NUMBERS = "3,813,376"
RANK = 16
MEMORY_GIB = 1.02
STEPS_DONE = "1,000"
BATCH = 4
RECIPE_STEPS = "20,000"
RECIPE_BATCH = 64
# 20,000 x 64 = 1,280,000 examples against 1,000 x 4 = 4,000, which is 320
# times as many. The README calls this "a small fraction"; the ratio is the
# arithmetic of the two settings it names.
RECIPE_RATIO = 320


def _tint(colour: str, towards_white: float) -> tuple[float, float, float]:
    """A pale version of a palette colour, for a band or a box fill.

    Blending with white rather than setting an alpha, because a band and a box
    sit on top of each other and a stack of transparent fills darkens.
    """
    red, green, blue = mcolors.to_rgb(colour)
    return tuple(channel + (1.0 - channel) * towards_white for channel in (red, green, blue))


class Sheet:
    """One chart, with its vertical arithmetic done in inches rather than by eye.

    Both axes carry the same scale: a hundred units across the figure, and as
    many units up it as the figure is tall in proportion. So a height worked out
    from a font size and a line count is a height that is right, and a box is
    built from the text it has to hold rather than from a number somebody
    guessed. Everything is placed from the top down, each box returning the
    height its own bottom edge reached, which is what stops two pieces of text
    ever being given the same place.
    """

    LEFT = 3.0
    RIGHT = 97.0

    # The panel is told to fill the figure, all but a strip at the top for the
    # title. Left at matplotlib's default margins, a hundred units across would
    # be a different length from a hundred units up, and a box height worked out
    # from a font size would come out about a third too short — which is exactly
    # how text ends up printed over the edge of its own box.
    FOR_TITLE = 0.95

    def __init__(self, width_inches: float, height_inches: float) -> None:
        self.figure, self.axis = new(width_inches, height_inches)
        self.axis.set_position((0.0, 0.0, 1.0, self.FOR_TITLE))
        self.unit = 100.0 / width_inches                      # units per inch
        self.top = 100.0 * height_inches * self.FOR_TITLE / width_inches
        bare(self.axis)
        self.axis.set_xlim(0.0, 100.0)
        self.axis.set_ylim(0.0, self.top)
        self._bands: list[tuple] = []

    # -------------------------------------------------------------- measuring
    def line_height(self, size: float) -> float:
        """How tall one line of text of this size is, in this chart's units."""
        return 1.45 * (size / 72.0) * self.unit

    def text_height(self, text: str, size: float = NOTE_SIZE) -> float:
        return (text.count("\n") + 1) * self.line_height(size)

    def box_height(self, text: str, size: float = NOTE_SIZE) -> float:
        """A box's height: its text, plus about six points of air above and below."""
        return self.text_height(text, size) + 0.18 * self.unit

    # ---------------------------------------------------------------- drawing
    def box(
        self,
        x: float,
        top: float,
        width: float,
        text: str,
        *,
        edge: str = INK,
        face=PAPER,
        size: float = NOTE_SIZE,
        ink: str = INK,
        weight: str = "normal",
        lw: float = 1.2,
        height: float | None = None,
    ) -> float:
        """A rounded box hanging from ``top``. Returns where its bottom edge is."""
        height = self.box_height(text, size) if height is None else height
        bottom = top - height
        self.axis.add_patch(
            FancyBboxPatch(
                (x - width / 2.0, bottom),
                width,
                height,
                boxstyle="round,pad=0,rounding_size=1.0",
                linewidth=lw,
                edgecolor=edge,
                facecolor=face,
                zorder=3,
            )
        )
        self.axis.text(
            x,
            bottom + height / 2.0,
            text,
            ha="center",
            va="center",
            fontsize=size,
            color=ink,
            weight=weight,
            linespacing=1.45,
            zorder=5,
        )
        return bottom

    def row(
        self,
        top: float,
        centres: list[float],
        width: float,
        texts: list[str],
        **kwargs,
    ) -> float:
        """Several boxes side by side, all as tall as the tallest text among them."""
        size = kwargs.get("size", NOTE_SIZE)
        height = max(self.box_height(text, size) for text in texts)
        for x, text in zip(centres, texts):
            self.box(x, top, width, text, height=height, **kwargs)
        return top - height

    def arrow(self, start, end, *, colour: str = INK, lw: float = 1.4,
              dashed: bool = False) -> None:
        self.axis.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=13,
                linewidth=lw,
                color=colour,
                linestyle=(0, (4, 3)) if dashed else "solid",
                shrinkA=0,
                shrinkB=0,
                zorder=6,
            )
        )

    def link(
        self,
        top: float,
        *,
        x: float = 50.0,
        gap: float = 2.6,
        note: str | None = None,
        note_x: float = 38.0,
        note_colour: str = MUTED,
        note_weight: str = "normal",
        colour: str = INK,
    ) -> float:
        """A downward arrow into the next box, with an optional note beside it.

        The gap is widened to hold the note, so a note can never be written
        over the box above it or the box below it, and the arrow is moved left
        of centre when there is a note so that it cannot run through the words.
        """
        if note is not None:
            gap = max(gap, self.text_height(note) + 1.8)
            x = min(x, 34.0)
        bottom = top - gap
        self.arrow((x, top), (x, bottom), colour=colour)
        if note is not None:
            self.axis.text(
                note_x,
                top - gap / 2.0,
                note,
                ha="left",
                va="center",
                fontsize=NOTE_SIZE,
                color=note_colour,
                weight=note_weight,
                linespacing=1.45,
                zorder=7,
            )
        return bottom

    def note(self, x: float, y: float, text: str, *, colour: str = MUTED,
             size: float = NOTE_SIZE, ha: str = "left", weight: str = "normal",
             rotation: float = 0.0) -> float:
        """A line or two of text with no box. Returns the bottom of the text."""
        self.axis.text(
            x,
            y - self.text_height(text, size) / 2.0,
            text,
            ha=ha,
            va="center",
            fontsize=size,
            color=colour,
            weight=weight,
            linespacing=1.45,
            rotation=rotation,
            zorder=7,
        )
        return y - self.text_height(text, size)

    def band(self, top: float, bottom: float, colour: str, label: str) -> None:
        """Remember a lane of the chart. The lanes are drawn last, underneath."""
        self._bands.append((top, bottom, colour, label))

    def rule(self, y: float) -> None:
        self.axis.plot([self.LEFT, self.RIGHT], [y, y], color=MUTED, lw=0.9,
                       ls=(0, (5, 4)), zorder=1)

    def finish(self, title: str, name: str) -> None:
        for top, bottom, colour, label in self._bands:
            self.axis.add_patch(
                Rectangle(
                    (self.LEFT, bottom),
                    self.RIGHT - self.LEFT,
                    top - bottom,
                    facecolor=_tint(colour, 0.90),
                    edgecolor=colour,
                    linewidth=1.0,
                    zorder=1,
                )
            )
            self.axis.text(
                self.LEFT + 4.0,
                (top + bottom) / 2.0,
                label,
                rotation=90,
                ha="center",
                va="center",
                fontsize=LABEL_SIZE,
                color=colour if colour != MUTED else INK,
                weight="bold",
                zorder=2,
            )
        self.axis.set_title(title, fontsize=TITLE_SIZE, color=INK, pad=12)
        save(self.figure, name)


# --------------------------------------------------------------------------- #
# Solution 4, chart 1: collecting, fitting, planning
# --------------------------------------------------------------------------- #


def worldmodel_what_it_does() -> None:
    """Solution 4 end to end, in the three stages it really has.

    The three stages happen at three different times — once, once, and before
    every single push the arm makes — so they are drawn as three lanes rather
    than as one chain of eleven boxes. The planning lane is the long one on
    purpose: it is where this solution spends its run time.
    """
    sheet = Sheet(11.6, 13.4)
    wide = 70.0
    y = sheet.top - 3.0

    # ------------------------------------------------- collecting the pushes
    collect_top = y
    y = sheet.box(
        50.0, y, wide,
        f"Round one: {ROUND_ONE_PUSHES} pushes are made at random on {ROUND_ONE_TABLES} tables in the simulator.\n"
        "Every example is one push really made — look, push, look again.",
    )
    y = sheet.link(
        y,
        note="The push is made because nobody can say in advance what it will do. The\n"
             "friction between a glass and this table is not measured anywhere in the cell.",
    )
    y = sheet.box(
        50.0, y, wide,
        f"Round two: {ROUND_TWO_PUSHES} more pushes on {ROUND_TWO_TABLES} new tables, mostly chosen by the planner\n"
        "using the round-one model. The planner finds the pushes that model is wrong\n"
        "about in its own favour, and making those pushes fills exactly those holes.",
    )
    y = sheet.link(y)
    y = sheet.box(
        50.0, y, wide,
        "Nobody labels any of it. The answer to every example is what the second look\n"
        "found, so the model is fitted to predict what the camera will report rather\n"
        "than what the simulator knows.",
        edge=GOOD, face=_tint(GOOD, 0.88), lw=1.6,
    )
    sheet.band(collect_top + 1.4, y - 1.4, MUTED, "collecting, once")

    # -------------------------------------------------------- fitting the five
    y = sheet.link(y, gap=3.4)
    fit_top = y
    y = sheet.box(
        50.0, y, wide,
        f"{COPIES} copies of the same small network are trained on those {ALL_PUSHES} pushes, each\n"
        f"from its own random starting weights. Each copy answers one question: given\n"
        f"this table and this push, what does the table look like afterwards. {INPUTS} numbers\n"
        f"in — the glasses as the camera measured them, and the push — and {OUTPUTS} out: a\n"
        f"displacement for every glass, whether anything toppled, and whether the jaw\n"
        f"was blocked on the way down. About {TRAIN_MINUTES} minutes on a laptop processor.",
        edge=GLASS, face=_tint(GLASS, 0.80), size=LABEL_SIZE, lw=1.8,
    )
    sheet.band(fit_top + 1.4, y - 1.4, GLASS, "fitting, once")

    # ------------------------------------------------------------- planning
    y = sheet.link(y, gap=3.4)
    plan_top = y
    draw_top = y
    y = sheet.box(
        50.0, y, wide,
        "Candidate pushes are drawn for every crowded glass: which way the jaw points,\n"
        "where across the glass it meets it, and how far it travels.",
    )
    y = sheet.link(y)
    y = sheet.box(
        50.0, y, wide,
        f"Every candidate is put to all {COPIES} copies at once. Asking the model is arithmetic,\n"
        "so a search that would be reckless against the table is ordinary against it.",
    )
    y = sheet.link(y)
    y = sheet.box(
        50.0, y, wide,
        f"A candidate is thrown away if any one copy gives it more than a {TOPPLE_LIMIT} chance of\n"
        f"toppling something — on the table as seen, and on {JITTERS} copies of it moved by about\n"
        "the camera's error, so that a push which only looks safe by luck does not survive.",
        edge=WARN, face=_tint(WARN, 0.88), lw=1.6,
    )
    y = sheet.link(y)
    y = sheet.box(
        50.0, y, wide,
        "A candidate is thrown away if the predicted table breaks the map: a glass it moves\n"
        "lands outside the zone glasses may stand in, or the jaw leaves the arm's reach.\n"
        "That map is written-down arithmetic, because reach is not the same in every\n"
        "direction and the model was never shown it.",
        edge=WARN, face=_tint(WARN, 0.88), lw=1.6,
    )
    y = sheet.link(y)
    y = sheet.box(
        50.0, y, wide,
        "The survivors are scored on the table the model predicts for them: how much clear\n"
        "room is still missing around every glass, plus a small penalty for each millimetre\n"
        "pushed, so the shortest push that does the job wins.",
    )
    y = sheet.link(y)
    refine_top = y
    y = sheet.box(
        50.0, y, wide,
        f"A sampling search refines the good ones. {FIRST_DRAWS} draws spread over the whole range,\n"
        f"then {LATER_DRAWS} more in each of three further rounds, each round drawn around the best\n"
        f"{ELITES} of the round before — about {CANDIDATES} candidates for every crowded glass.",
    )
    refine_bottom = y

    # the loop back: later rounds draw from where the good draws were
    riser = 91.0
    sheet.axis.plot([50.0 + wide / 2.0, riser],
                    [(refine_top + refine_bottom) / 2.0, (refine_top + refine_bottom) / 2.0],
                    color=INK, lw=1.2, ls=(0, (4, 3)), zorder=6)
    sheet.axis.plot([riser, riser],
                    [(refine_top + refine_bottom) / 2.0, draw_top - 2.0],
                    color=INK, lw=1.2, ls=(0, (4, 3)), zorder=6)
    sheet.arrow((riser, draw_top - 2.0), (50.0 + wide / 2.0, draw_top - 2.0), dashed=True)
    sheet.note(
        riser - 1.6, (refine_top + draw_top) / 2.0,
        f"{ROUNDS} rounds in all",
        colour=INK, ha="center", rotation=90, size=NOTE_SIZE - 0.6,
    )

    y = sheet.link(y, gap=3.0)
    y = sheet.box(
        50.0, y, wide,
        "The best push over all the crowded glasses is handed to the examiner, and only\n"
        "that one push is made. Then the arm looks again and the whole search runs afresh,\n"
        "so whatever the model got wrong is measured away instead of being inherited.",
        edge=GOOD, face=_tint(GOOD, 0.84), size=LABEL_SIZE, lw=1.8, weight="bold",
    )
    sheet.band(plan_top + 1.4, y - 1.4, GOOD, "planning, before every push the arm makes")

    sheet.note(
        50.0, y - 3.2,
        "Nothing in the chain holds a friction value or a tipping rule. What a push does is a regularity in the\n"
        "recorded pushes, and what counts as a good table is plain arithmetic kept outside the model.",
        colour=INK, ha="center",
    )

    sheet.finish(
        "Solution 4: thousands of recorded pushes, five copies of one network, and a search run before every push",
        "worldmodel-flow-what-it-does.png",
    )


# --------------------------------------------------------------------------- #
# Solution 4, chart 2: what the five copies are for
# --------------------------------------------------------------------------- #


def worldmodel_the_five_copies() -> None:
    """Why five copies, how their disagreement is spent, and where it fails.

    The disagreement between copies is the most transferable idea in solution
    4, so it gets a picture of its own. The limit is drawn on the same sheet
    rather than left to the prose, because a measure of ignorance that can
    itself be ignorant is a thing a reader has to be told about in the same
    breath.
    """
    sheet = Sheet(11.4, 8.6)
    y = sheet.top - 3.0

    y = sheet.box(
        50.0, y, 62.0,
        f"One training set: the {ALL_PUSHES} recorded pushes, every one of them look, push, look again",
        size=LABEL_SIZE, face=_tint(MUTED, 0.90), edge=MUTED,
    )
    fan_from = y

    copies_top = y - 5.0
    centres = [18.0, 34.0, 50.0, 66.0, 82.0]
    for x in centres:
        sheet.arrow((50.0, fan_from), (x, copies_top))
    y = sheet.row(
        copies_top, centres, 14.0,
        [f"copy {n}\nits own random\nstarting weights" for n in range(1, COPIES + 1)],
        edge=GLASS, face=_tint(GLASS, 0.84),
    )
    y = sheet.note(
        50.0, y - 2.2,
        f"The same question goes to all {COPIES}, and {COPIES} answers come back.",
        colour=INK, ha="center", weight="bold",
    )

    split = y - 1.6
    left, right, column = 27.0, 73.0, 42.0
    branch_top = split - 3.0
    sheet.arrow((50.0, split), (left, branch_top))
    sheet.arrow((50.0, split), (right, branch_top))

    agree = sheet.box(
        left, branch_top, column,
        "Where the five agree, the training data\n"
        "pinned this kind of push down. The copies\n"
        "have seen pushes like this one.",
        edge=GOOD, face=_tint(GOOD, 0.86), lw=1.6,
    )
    disagree = sheet.box(
        right, branch_top, column,
        "Where they disagree, the data did not pin it\n"
        "down, and each copy filled the gap with\n"
        "whatever its own starting weights led to.",
        edge=GLASS, face=_tint(GLASS, 0.82), lw=1.6,
    )
    y = min(agree, disagree)

    use_top = y - 3.4
    sheet.arrow((left, y), (left, use_top))
    sheet.arrow((right, y), (right, use_top))
    first = sheet.box(
        left, use_top, column,
        "For the displacements the planner takes the\n"
        "copies' average. There the spread is only\n"
        "accuracy, and the next look corrects it.",
    )
    second = sheet.box(
        right, use_top, column,
        f"For toppling it takes the worst copy's chance,\n"
        f"not the average. Any copy giving a push more\n"
        f"than a {TOPPLE_LIMIT} chance takes it out of consideration.",
        edge=WARN, lw=1.4,
    )
    y = min(first, second)

    y = sheet.note(
        50.0, y - 2.2,
        "The two errors being traded are not comparable: a refused push costs a refusal, and a push that tips a glass\n"
        f"costs the glass. The whole measurement costs the training of four more small networks — all {COPIES} of them in\n"
        f"about {TRAIN_MINUTES} minutes on a laptop processor.",
        colour=INK, ha="center",
    )

    sheet.rule(y - 2.0)
    y = sheet.note(
        50.0, y - 3.4,
        "The honest limit: agreement is not knowledge",
        colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold",
    )
    y = sheet.box(
        50.0, y - 1.6, 84.0,
        "Where the training data is thin in a way the copies did not notice, all five agree and are wrong together.\n"
        f"On the {TUNING_TABLES} tuning tables {TUNING_TOPPLED} glass went over, and the record says the model had rated as safe every topple\n"
        "it missed: the jaw met a stemmed glass's stem under the bowl and lifted it over, the jaw's body clipped a\n"
        "neighbour behind, and a tapered glass tipped on its own.",
        edge=WARN, face=_tint(WARN, 0.88), lw=1.8,
    )
    sheet.note(
        50.0, y - 2.6,
        "A lower limit than one in a hundred does not remove those. It only refuses more. They need more recorded pushes.",
        colour=INK, ha="center",
    )

    sheet.finish(
        "Solution 4: what the five copies are for, and the one thing their agreement cannot tell you",
        "worldmodel-flow-the-five-copies.png",
    )


# --------------------------------------------------------------------------- #
# Solution 5: the shortest chain in the book
# --------------------------------------------------------------------------- #


def smolvla_what_it_does() -> None:
    """Solution 5, drawn short because it is short.

    Four boxes between the camera and the table being changed, and no training
    step anywhere. The chart's shape is part of what it says, so nothing is
    added to it that the solution does not contain.
    """
    sheet = Sheet(10.4, 6.2)
    y = sheet.top - 3.0

    centres = [19.0, 50.0, 81.0]
    y = sheet.row(
        y, centres, 28.0,
        [
            f"The rendered view of the table\nfrom the top: {VIEW_PIXELS} pixels of\n"
            f"colour from a camera {VIEW_HEIGHT_MM} mm\nabove the glass zone, looking\nstraight down",
            "One instruction in plain English,\nthe same line every table:\n"
            '"the glasses are too close together,\npush them apart"',
            # The model's slot is for joint readings. What this cell puts in it
            # is where the jaw is, which joining.to_state fills from the jaw's
            # pose, so the picture says what is really handed over.
            "Where the jaw is, in the slot\nthe model keeps for the arm's\nown joint readings",
        ],
        edge=GLASS, face=_tint(GLASS, 0.86),
    )

    model_top = y - 3.2
    for x in centres:
        sheet.arrow((x, y), (x, model_top))
    y = sheet.box(
        50.0, model_top, 76.0,
        f"The downloaded model: SmolVLA, {SMOLVLA_PARAMETERS} numbers, used exactly as it arrives.\n"
        "It was fitted on recordings of other people's robots being driven by people.",
        edge=INK, face=_tint(MUTED, 0.88), size=LABEL_SIZE, lw=1.8,
    )
    y = sheet.link(y)
    y = sheet.box(
        50.0, y, 76.0,
        f"It returns a run of {CHUNK_WAYPOINTS} actions, predicted together in one pass.",
        size=LABEL_SIZE,
    )
    y = sheet.link(
        y,
        note="The actions arrive in somebody else's units. The model was fitted on\n"
             "other arms, so reading them as waypoints for this jaw is a convention\n"
             "somebody chose, written down once and used by solutions 5 and 6 alike.",
        note_colour=WARN, note_weight="bold",
    )
    y = sheet.box(
        50.0, y, 76.0,
        "An agreed interpretation reads those actions as waypoints for this jaw.",
        edge=WARN, face=_tint(WARN, 0.88), lw=1.6, size=LABEL_SIZE,
    )
    y = sheet.link(y)
    y = sheet.box(
        50.0, y, 76.0,
        "The examiner carries the waypoints out directly, rather than through the push macro\n"
        "it owns. The table changes, the arm looks again, and the model is asked once more,\n"
        "until every glass has its room or the push budget is spent.",
        edge=GOOD, face=_tint(GOOD, 0.86), lw=1.6,
    )

    y = sheet.box(
        50.0, y - 3.0, 76.0,
        "There is no training step, no data collection and no fitted parameter anywhere.\n"
        "If a number in this solution came from somewhere, it came from somebody else's robots.",
        edge=INK, face=PAPER, size=LABEL_SIZE, lw=1.8, weight="bold",
    )

    sheet.finish(
        "Solution 5: a picture, one sentence and the arm's pose go in, and jaw waypoints come out",
        "smolvla-flow-what-it-does.png",
    )


# --------------------------------------------------------------------------- #
# Solution 6, chart 1: the same chain with a training step in front of it
# --------------------------------------------------------------------------- #


def smolvla_finetuned_what_it_does() -> None:
    """Solution 6: solution 5's chain, with training put in front.

    Two lanes, because the two halves happen at different times and only one
    of them is what separates this solution from its partner. The run-time lane
    is deliberately the same shape as solution 5's chart.
    """
    sheet = Sheet(11.4, 9.6)
    wide = 70.0
    y = sheet.top - 3.0

    train_top = y
    y = sheet.box(
        50.0, y, wide,
        "The teacher is solution 2: geometry proposes candidate pushes and a fitted ranker\n"
        "picks one. It is run on the examiner over the training half of the tables, and the\n"
        "examiner writes down the path the jaw really followed on every push it makes.\n"
        f"Measured: {TRAINING_TABLES} training tables, {COLLECT_MINUTES} minutes of simulator time, {DEMONSTRATIONS} demonstrations\n"
        f"from {DEMONSTRATION_TABLES} of those tables. Nobody held a controller, so the demonstrations are free.",
    )
    y = sheet.link(y)
    y = sheet.box(
        50.0, y, wide,
        f"The recordings where something went wrong are dropped: of {REAL_PUSHES} real pushes, {DISCARDED} were\n"
        f"discarded, {DISCARDED_TOPPLED} because they toppled a glass and {DISCARDED_OUT_OF_ZONE} because it pushed one out of the zone.\n"
        "What is dropped is what the teacher handled badly, so the student is fitted on the easy\n"
        "half of its teacher's experience. Here that half is four tenths of one per cent of it.",
        edge=WARN, face=_tint(WARN, 0.88), lw=1.6,
    )
    y = sheet.link(y)
    y = sheet.box(
        50.0, y, wide,
        "A low-rank correction is fitted on those demonstrations, so that the chunks the\n"
        "model emits come out in this cell's own range rather than the range the borrowed\n"
        f"recordings happened to use. Every one of the {SMOLVLA_PARAMETERS} borrowed numbers stays\n"
        f"where it is, and {MOVING_NUMBERS} new ones are learned beside them.",
        edge=GLASS, face=_tint(GLASS, 0.80), size=LABEL_SIZE, lw=1.8,
    )
    sheet.band(train_top + 1.4, y - 1.4, GLASS, "training, once")

    y = sheet.note(
        50.0, y - 2.6,
        "The correction is folded into the borrowed weights, and from here on the chain is solution 5's.",
        colour=INK, ha="center",
    )
    y -= 1.6
    run_top = y
    centres = [22.0, 50.0, 78.0]
    y = sheet.row(
        y, centres, 26.0,
        [
            f"The rendered view of the table\nfrom the top, {VIEW_PIXELS} pixels\n"
            f"from {VIEW_HEIGHT_MM} mm straight above",
            "One instruction in plain English,\nthe same line every table, so\nthat channel carries nothing",
            "The arm's own pose, which is the\nsame six numbers every time\nbecause the jaw is parked\nbetween actions",
        ],
        edge=MUTED, face=_tint(MUTED, 0.90),
    )
    model_top = y - 3.0
    for x in centres:
        sheet.arrow((x, y), (x, model_top))
    y = sheet.box(
        50.0, model_top, wide,
        f"The corrected model returns an action chunk: {CHUNK_WAYPOINTS} consecutive jaw waypoints\n"
        "predicted together in one pass, and the whole chunk is committed to before the\n"
        "arm looks again.",
        size=LABEL_SIZE, lw=1.6,
    )
    y = sheet.link(y)
    y = sheet.box(
        50.0, y, wide,
        "The shared geometry refuses the glasses that tip before they slide, and a chunk\n"
        "whose path would reach one of those is not carried out. The model has no field in\n"
        "it for a rule, so it cannot be the thing that refuses a glass.",
        edge=WARN, face=_tint(WARN, 0.88), lw=1.6,
    )
    y = sheet.link(y)
    y = sheet.box(
        50.0, y, wide,
        "The examiner carries the rest of the chunk out directly, because a chunk needs no\n"
        "expansion. The arm looks again, and the loop repeats until the table is done or\n"
        "the push budget is spent.",
        edge=GOOD, face=_tint(GOOD, 0.86), lw=1.6,
    )
    sheet.band(run_top + 1.4, y - 1.4, GOOD, "at run time, for every chunk")

    sheet.note(
        50.0, y - 3.2,
        "Everything but the training is solution 5's: the same library, the same downloaded weights, the same picture, the\n"
        "same sentence, the same reading of an action into waypoints, the same loop and the same marking.",
        colour=INK, ha="center",
    )

    sheet.finish(
        "Solution 6: solution 5's chain with a training step put in front of it",
        "smolvla-finetuned-flow-what-it-does.png",
    )


# --------------------------------------------------------------------------- #
# Solution 6, chart 2: what the correction is
# --------------------------------------------------------------------------- #


def smolvla_finetuned_the_correction() -> None:
    """What low-rank adaptation is, in one drawing and three statements.

    The whole affordability of solution 6 rests on this, so the tables are
    drawn at something like their real proportions: the borrowed table is a
    square, and the two learned tables are thin, because thin is the entire
    point. The caveat about how little training was actually spent sits on the
    same sheet, because the drawing explains why so little was affordable.
    """
    sheet = Sheet(11.0, 8.4)
    y = sheet.top - 4.0

    # ------------------------------------------------------- the one equation
    square = 22.0
    thin = 5.0
    borrowed_x, down_x, out_x = 23.0, 47.0, 70.0
    row_top = y
    row_bottom = y - square

    def table(x_left, width, height, colour, label):
        sheet.axis.add_patch(
            Rectangle(
                (x_left, row_top - height),
                width,
                height,
                facecolor=_tint(colour, 0.82),
                edgecolor=colour,
                linewidth=1.6,
                zorder=3,
            )
        )
        sheet.note(x_left + width / 2.0, row_top - height - 1.4, label,
                   colour=INK, ha="center", size=NOTE_SIZE - 0.4)

    table(borrowed_x - square / 2.0, square, square, MUTED,
          "one borrowed table of weights,\nleft exactly as it is")
    sheet.note(39.5, (row_top + row_bottom) / 2.0, "+", colour=INK,
               size=TITLE_SIZE + 6.0, ha="center", weight="bold")
    table(down_x - thin / 2.0, thin, square, GLASS,
          f"squeeze the incoming\nlist to {RANK} numbers")
    sheet.note(54.0, (row_top + row_bottom) / 2.0, "×", colour=INK,
               size=TITLE_SIZE + 4.0, ha="center", weight="bold")
    sheet.axis.add_patch(
        Rectangle(
            (out_x - square / 2.0, (row_top + row_bottom) / 2.0 - thin / 2.0),
            square,
            thin,
            facecolor=_tint(GLASS, 0.82),
            edgecolor=GLASS,
            linewidth=1.6,
            zorder=3,
        )
    )
    sheet.note(out_x, (row_top + row_bottom) / 2.0 - thin / 2.0 - 1.4,
               "expand those numbers\nback to full width",
               colour=INK, ha="center", size=NOTE_SIZE - 0.4)
    sheet.note(88.0, (row_top + row_bottom) / 2.0,
               "the two thin\ntables are the\ncorrection",
               colour=GLASS, ha="center", weight="bold", size=NOTE_SIZE - 0.4)

    y = row_bottom - 6.4
    y = sheet.box(
        50.0, y, 84.0,
        "The product of the two thin tables is as wide as the table it corrects, so the layer still does the same\n"
        f"work. What it cannot be is an arbitrary table: forced through a squeeze {RANK} numbers wide, the correction\n"
        f"is a sum of {RANK} patterns rather than any table whatever. Where the new task is far from the old one, which\n"
        "this cell is, a correction that could move the whole table would go further — so what the pair of\n"
        "solutions 5 and 6 measures is a lower bound on what fine-tuning could buy.",
    )

    # ------------------------------------------------- what it buys, measured
    y = sheet.note(
        50.0, y - 3.0,
        "What that buys, measured on this laptop",
        colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold",
    )
    left, right, column = 27.0, 73.0, 44.0
    pair_top = y - 1.8
    first = sheet.box(
        left, pair_top, column,
        "Only the correction carries gradients and the\n"
        f"optimiser's running averages: {MOVING_NUMBERS} numbers\n"
        f"move and {SMOLVLA_PARAMETERS} sit still. So what has\n"
        "to be held is the model plus a little, and the\n"
        f"training held {MEMORY_GIB} GiB. Nothing was rented.",
        edge=GOOD, face=_tint(GOOD, 0.86), lw=1.6,
    )
    second = sheet.box(
        right, pair_top, column,
        "Afterwards the two thin tables are multiplied\n"
        "out and added into the borrowed table, leaving\n"
        "one table of the original size. So running the\n"
        "fine-tuned model costs exactly what running\n"
        "the downloaded one costs, to the arithmetic.",
        edge=GOOD, face=_tint(GOOD, 0.86), lw=1.6,
    )
    y = min(first, second)

    # ------------------------------------------------------------ the caveat
    sheet.rule(y - 2.2)
    y = sheet.note(
        50.0, y - 3.6,
        "The caveat that belongs beside every number this solution reports",
        colour=INK, size=LABEL_SIZE + 1.0, ha="center", weight="bold",
    )
    y = sheet.box(
        50.0, y - 1.6, 84.0,
        f"What ran here is {STEPS_DONE} steps at a batch of {BATCH}. The recipe this model's own library publishes spends\n"
        f"{RECIPE_STEPS} steps at a batch of {RECIPE_BATCH}, which is {RECIPE_RATIO} times as many examples. So this is about one part in\n"
        "three hundred of the training the recipe asks for, and the memory was never the thing that stopped it:\n"
        "a training step took about four seconds on this laptop's own graphics processor.",
        edge=WARN, face=_tint(WARN, 0.88), lw=1.8,
    )

    sheet.finish(
        "Solution 6: the borrowed weights stay, a small correction is learned beside them, and afterwards it folds in",
        "smolvla-finetuned-flow-the-correction.png",
    )


def main() -> None:
    worldmodel_what_it_does()
    worldmodel_the_five_copies()
    smolvla_what_it_does()
    smolvla_finetuned_what_it_does()
    smolvla_finetuned_the_correction()


if __name__ == "__main__":
    main()
