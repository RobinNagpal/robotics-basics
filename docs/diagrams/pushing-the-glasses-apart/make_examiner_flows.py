"""The flow charts for the examiner of pushing the glasses apart.

The examiner document was one page of ten sections and a single picture, so a
reader met its whole argument as prose. These charts carry the parts of it that
are shapes rather than sentences: what is held still, the three calls a solution
may make, what is handed over against what is kept back, and why the marking
looks at the outcome rather than at the action.

    examiner-flow-what-is-held-still.png   the input, the output and the marking
    examiner-flow-the-three-calls.png      look, push and take, and the loop
    examiner-flow-given-and-kept.png       the readings handed over, and the truth kept back
    examiner-flow-outcome-not-action.png   why a push is marked by what it did

Every number written into these pictures is read out of ``code/src/`` and the
constant that holds it is named in a comment beside it.

Run from code/:

    pixi run python ../docs/diagrams/pushing-the-glasses-apart/make_examiner_flows.py
"""

from __future__ import annotations

from make_solution_flows_a import (
    GAP,
    GOOD,
    GRIP_ROOM_MM,
    INK,
    LABEL_SIZE,
    MUTED,
    NOTE_SIZE,
    PUSHES_PER_GLASS,
    PUSHES_PER_TABLE,
    TEST_FROM,
    WARN,
    _tint,
    arrow,
    band,
    box,
    elbow,
    finish,
    note,
    save,
    sheet,
    title,
)

GLASS = "#3b82c4"


# --------------------------------------------------------------------------- #
# 1. what the examiner holds still
# --------------------------------------------------------------------------- #


def what_is_held_still() -> None:
    """The three fixed things, and the one place a solution is free.

    The chart exists to make one claim visible: everything a solution may change
    sits between the input and the output, so a difference in the marking is a
    difference in the method and nothing else.
    """
    width, height = 10.2, 5.1
    figure, axis = sheet(width, height)
    chain_w = 7.0
    chain_x = width / 2.0

    y = title(figure, axis, width, height - 0.12,
              "What the examiner holds still, and the one part it does not") - 0.30

    y = box(figure, axis, chain_x, y, chain_w,
            "The same tables, in the same order, measured the same way",
            edge=MUTED, face=_tint(MUTED, 0.88))
    arrow(axis, (chain_x, y), (chain_x, y - GAP))

    y = box(figure, axis, chain_x, y - GAP, chain_w,
            "Whatever the solution does with them",
            edge=GLASS, face=_tint(GLASS, 0.80), weight="bold", size=LABEL_SIZE, lw=1.8)
    free_bottom = y
    note(axis, chain_x + chain_w / 2.0 + 0.18, y + 0.42,
         "the only part\nthat varies", colour=GLASS, size=NOTE_SIZE - 0.4,
         weight="bold", figure=figure)
    arrow(axis, (chain_x, y), (chain_x, y - GAP))

    y = box(figure, axis, chain_x, y - GAP, chain_w,
            "The same kind of answer, carried out by the same machinery",
            edge=MUTED, face=_tint(MUTED, 0.88))
    arrow(axis, (chain_x, y), (chain_x, y - GAP))

    y = box(figure, axis, chain_x, y - GAP, chain_w,
            "The same counts, computed the same way",
            edge=MUTED, face=_tint(MUTED, 0.88))
    arrow(axis, (chain_x, y), (chain_x, y - GAP))

    y = box(figure, axis, chain_x, y - GAP, chain_w,
            "One scorecard, comparable with the other five",
            edge=GOOD, face=_tint(GOOD, 0.82), weight="bold", size=LABEL_SIZE, lw=1.8)

    y = note(axis, chain_x, y - 0.30,
             "So a difference between two scorecards belongs to the method.",
             colour=INK, size=NOTE_SIZE, ha="center", weight="bold", figure=figure)
    finish(figure, axis, "examiner-flow-what-is-held-still.png", y - 0.10)
    save(figure, "examiner-flow-what-is-held-still.png")


# --------------------------------------------------------------------------- #
# 2. the three calls
# --------------------------------------------------------------------------- #


def the_three_calls() -> None:
    """look, push and take: the whole of what a solution may do to a table.

    Drawn as the loop it is, because the budget is what ends it and a reader who
    sees the loop sees why a solution has to choose what to spend a push on.
    """
    width, height = 12.4, 4.4
    figure, axis = sheet(width, height)
    chain_w = 5.8
    chain_x = 4.2

    y = title(figure, axis, width, height - 0.12,
              "The three calls, and the budget that ends the loop") - 0.30

    y = box(figure, axis, chain_x, y, chain_w,
            "look(): one reading per glass still standing",
            edge=GLASS, face=_tint(GLASS, 0.86))
    look_mid = y + 0.22
    arrow(axis, (chain_x, y), (chain_x, y - GAP))

    y = box(figure, axis, chain_x, y - GAP, chain_w,
            "The solution decides what to do",
            edge=INK)
    arrow(axis, (chain_x, y), (chain_x, y - GAP))

    y = box(figure, axis, chain_x, y - GAP, chain_w,
            "push(): the jaw follows the path it was given",
            edge=GLASS, face=_tint(GLASS, 0.86))
    push_bottom = y
    arrow(axis, (chain_x, y), (chain_x, y - GAP))

    y = box(figure, axis, chain_x, y - GAP, chain_w,
            f"Any pushes left? At most {PUSHES_PER_GLASS} on one glass "
            f"and {PUSHES_PER_TABLE} on the table.",
            face=_tint(MUTED, 0.88), weight="bold", size=LABEL_SIZE)
    test_bottom = y
    test_mid = y + 0.24

    # yes: back to the top
    elbow(axis, (chain_x - chain_w / 2.0, test_mid), (chain_x - chain_w / 2.0, look_mid),
          by_way_of=chain_x - chain_w / 2.0 - 0.75, colour=GLASS)
    note(axis, chain_x - chain_w / 2.0 - 0.90, (test_mid + look_mid) / 2.0 + 0.16,
         "yes:\nlook again", colour=GLASS, size=NOTE_SIZE - 0.6, ha="right",
         weight="bold", figure=figure)

    # no: take
    end_x, end_w = 9.9, 4.3
    arrow(axis, (chain_x + chain_w / 2.0, test_mid), (end_x - end_w / 2.0, test_mid),
          colour=WARN)
    note(axis, chain_x + chain_w / 2.0 + 0.16, test_mid + 0.52, "no",
         colour=WARN, size=NOTE_SIZE - 0.6, weight="bold", figure=figure)
    box(figure, axis, end_x, test_mid + 0.40, end_w,
        "take(): the run is over,\nand the examiner marks it",
        edge=WARN, face=_tint(WARN, 0.86), weight="bold", size=LABEL_SIZE)

    y = note(axis, width / 2.0, test_bottom - 0.34,
             "A push is spent whether or not it helped, so choosing well is the whole job.",
             colour=INK, size=NOTE_SIZE, ha="center", weight="bold", figure=figure)
    finish(figure, axis, "examiner-flow-the-three-calls.png", y - 0.10)
    save(figure, "examiner-flow-the-three-calls.png")


# --------------------------------------------------------------------------- #
# 3. what is handed over and what is kept back
# --------------------------------------------------------------------------- #


def given_and_kept() -> None:
    """Two columns: the readings a solution may have, and the truth it may not.

    The two columns are the same table seen from two sides, which is the one
    case where two panels belong in one picture.
    """
    width, height = 11.4, 5.2
    figure, axis = sheet(width, height)
    col_w = 4.9
    left_x, right_x = 0.45 + col_w / 2.0, width - 0.45 - col_w / 2.0

    y = title(figure, axis, width, height - 0.12,
              "What a solution may read, and what the examiner keeps") - 0.34

    top = y
    note(axis, left_x, top, "Handed over", colour=GOOD, size=LABEL_SIZE + 1.0,
         ha="center", weight="bold", figure=figure)
    note(axis, right_x, top, "Kept back", colour=WARN, size=LABEL_SIZE + 1.0,
         ha="center", weight="bold", figure=figure)

    y_left = top - 0.42
    for text in (
        "where each glass stands",
        "how tall it is",
        "how wide it is at its widest",
        "how wide its foot is",
        "whether it is still standing",
        "a top-down picture, for the solutions that read pictures",
    ):
        y_left = box(figure, axis, left_x, y_left, col_w, text,
                     edge=GOOD, face=_tint(GOOD, 0.90)) - 0.14

    y_right = top - 0.42
    for text, hard in (
        ("the true position and shape of every glass", False),
        ("every glass's mass", False),
        ("the three friction coefficients", True),
    ):
        y_right = box(figure, axis, right_x, y_right, col_w, text,
                      edge=WARN, face=_tint(WARN, 0.90),
                      weight="bold" if hard else "normal") - 0.14

    y_right = note(axis, right_x, y_right - 0.16,
                   "Nothing in the cell measures friction,\nso hiding it is honest rather than unkind.",
                   colour=WARN, size=NOTE_SIZE, ha="center", figure=figure)

    y_left = note(axis, left_x, y_left - 0.16,
                  "Every reading carries the camera work's own measured error,\n"
                  "fresh on each look, and the same for all six on the first one.",
                  colour=INK, size=NOTE_SIZE, ha="center", figure=figure)

    finish(figure, axis, "examiner-flow-given-and-kept.png", min(y_left, y_right) - 0.10)
    save(figure, "examiner-flow-given-and-kept.png")


# --------------------------------------------------------------------------- #
# 4. the marking looks at the outcome
# --------------------------------------------------------------------------- #


def outcome_not_action() -> None:
    """Why the scorecard never reads the push, only what the push did."""
    width, height = 10.8, 3.6
    figure, axis = sheet(width, height)
    col_w = 4.6
    left_x, right_x = 0.45 + col_w / 2.0, width - 0.45 - col_w / 2.0

    y = title(figure, axis, width, height - 0.12,
              "The score is the outcome, never the action") - 0.34

    top = y
    note(axis, left_x, top, "What the examiner never asks",
         colour=WARN, size=LABEL_SIZE + 0.6, ha="center", weight="bold", figure=figure)
    note(axis, right_x, top, "What it counts instead",
         colour=GOOD, size=LABEL_SIZE + 0.6, ha="center", weight="bold", figure=figure)

    y_left = top - 0.40
    for text in ("Was that the push I would have chosen?",
                 "Did it come from a rule or from a model?",
                 "Did it match a demonstration?"):
        y_left = box(figure, axis, left_x, y_left, col_w, text,
                     edge=WARN, face=_tint(WARN, 0.90)) - 0.14

    y_right = top - 0.40
    for text in ("How many glasses can be gripped now?",
                 "How many pushes did that take?",
                 "Did anything fall over or leave the zone?"):
        y_right = box(figure, axis, right_x, y_right, col_w, text,
                      edge=GOOD, face=_tint(GOOD, 0.90)) - 0.14

    y = note(axis, width / 2.0, min(y_left, y_right) - 0.26,
             "A solution that reaches the rack by a route nobody expected scores exactly as well\n"
             "as one that followed the obvious route, which is what lets six different methods be compared at all.",
             colour=INK, size=NOTE_SIZE, ha="center", weight="bold", figure=figure)
    finish(figure, axis, "examiner-flow-outcome-not-action.png", y - 0.10)
    save(figure, "examiner-flow-outcome-not-action.png")


def main() -> None:
    what_is_held_still()
    the_three_calls()
    given_and_kept()
    outcome_not_action()


if __name__ == "__main__":
    main()
