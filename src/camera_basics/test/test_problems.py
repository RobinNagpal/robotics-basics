"""The two problems the doc works through must run, and print what it quotes."""

from camera_basics.camera import capture, ONE_BOX_SCENE, TABLE_SCENE, TOP_DOWN, WRIST
from camera_basics.problems import one_box, three_boxes


def test_part_1_finds_and_measures_the_one_box(capsys):
    one_box.main()
    printed = capsys.readouterr().out
    assert '74,176' in printed               # readings that landed on the table
    assert '(+0.064, +0.040)' in printed     # the red box, measured


def test_part_2_tells_three_boxes_apart_and_measures_each(capsys):
    three_boxes.main()
    printed = capsys.readouterr().out
    assert '68,897' in printed               # the table, now sharing with three boxes
    for measured in ('(+0.064, +0.040)', '(-0.060, +0.048)', '(-0.040, -0.062)'):
        assert measured in printed


def test_the_other_boxes_do_not_change_the_red_box_measurement():
    """Part 2 adds boxes but must not disturb what part 1 measured."""
    alone = capture(ONE_BOX_SCENE, WRIST, TOP_DOWN).measure('red')
    among_three = capture(TABLE_SCENE, WRIST, TOP_DOWN).measure('red')
    assert alone == among_three
