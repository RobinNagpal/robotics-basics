"""Unit tests for :mod:`camera_basics.camera`.

No rclpy anywhere: the camera is plain arithmetic, so it can be checked without
a ROS graph, and the checks below are the ones that catch real mistakes —
sign errors in the axes, a projection that does not invert, depth measured along
the wrong line.
"""

import math

from camera_basics.camera import (
    axes_to_quaternion,
    Box,
    CameraConfig,
    capture,
    CONFIGS,
    field_of_view_deg,
    focal_length_px,
    look_at,
    OPTICAL_FROM_BODY_QUATERNION,
    Scene,
    TABLE_SCENE,
    TOP_DOWN,
    WRIST,
)
import pytest

TOP_DOWN_HEIGHT_M = 0.40


# -- the lens --------------------------------------------------------------


def test_focal_length_matches_the_worked_example():
    assert focal_length_px(320, 60.0) == pytest.approx(160.0 / math.tan(math.radians(30.0)))
    assert focal_length_px(320, 60.0) == pytest.approx(277.128, abs=1e-3)


def test_field_of_view_inverts_focal_length():
    assert field_of_view_deg(320, focal_length_px(320, 60.0)) == pytest.approx(60.0)


def test_halving_the_field_of_view_roughly_doubles_the_focal_length():
    narrow = focal_length_px(320, 30.0)
    wide = focal_length_px(320, 60.0)
    assert narrow > 2.0 * wide * 0.9


def test_principal_point_is_the_middle_of_the_picture():
    assert (WRIST.cx, WRIST.cy) == (160.0, 120.0)


def test_resolution_alone_does_not_change_what_is_in_shot():
    """Resolution changes how finely the same view is sampled, nothing more."""
    hires, lowres = CONFIGS['hires'], CONFIGS['lowres']
    assert hires.coverage_m(1.0) == pytest.approx(lowres.coverage_m(1.0))
    assert hires.metres_per_pixel(1.0) < lowres.metres_per_pixel(1.0)


def test_coverage_grows_with_distance():
    close = WRIST.coverage_m(1.0)[0]
    far = WRIST.coverage_m(2.0)[0]
    assert far == pytest.approx(2.0 * close)


def test_vertical_field_of_view_follows_from_the_aspect_ratio():
    assert WRIST.vfov_deg < WRIST.hfov_deg
    assert WRIST.vfov_deg == pytest.approx(field_of_view_deg(240, WRIST.fy))


# -- projection and its inverse --------------------------------------------


def test_straight_ahead_lands_on_the_principal_point():
    assert WRIST.project((0.0, 0.0, 2.0)) == pytest.approx((WRIST.cx, WRIST.cy))


def test_twice_as_far_for_twice_the_offset_is_the_same_pixel():
    """The flattening: a pixel is a direction, not a place."""
    near = WRIST.project((0.1, 0.05, 1.0))
    far = WRIST.project((0.2, 0.10, 2.0))
    assert near == pytest.approx(far)


def test_nothing_behind_the_lens_has_a_pixel():
    assert WRIST.project((0.1, 0.0, -1.0)) is None
    assert WRIST.project((0.1, 0.0, 0.0)) is None


@pytest.mark.parametrize('pixel', [(0.5, 0.5), (160.0, 120.0), (212.5, 86.5), (319.5, 239.5)])
@pytest.mark.parametrize('depth_m', [0.2, 0.34, 2.5])
def test_deproject_then_project_is_a_round_trip(pixel, depth_m):
    point = WRIST.deproject(pixel[0], pixel[1], depth_m)
    assert WRIST.project(point) == pytest.approx(pixel)


def test_deprojected_depth_is_the_forward_component():
    _, _, z = WRIST.deproject(0.0, 0.0, 0.75)
    assert z == pytest.approx(0.75)


def test_ray_has_unit_forward_component():
    """This is what makes the ray caster's t come out as a depth."""
    assert WRIST.ray(37.0, 200.0)[2] == pytest.approx(1.0)


def test_contains_rejects_pixels_off_the_picture():
    assert WRIST.contains(0.0, 0.0)
    assert not WRIST.contains(-0.5, 10.0)
    assert not WRIST.contains(10.0, 240.0)


# -- where the camera is ---------------------------------------------------


def _dot(a, b):
    return sum(p * q for p, q in zip(a, b))


def test_look_at_axes_are_perpendicular_and_unit_length():
    pose = look_at((0.2, -0.1, 0.5), (0.0, 0.0, 0.0))
    for axis in (pose.right, pose.down, pose.forward):
        assert _dot(axis, axis) == pytest.approx(1.0)
    assert _dot(pose.right, pose.down) == pytest.approx(0.0, abs=1e-9)
    assert _dot(pose.right, pose.forward) == pytest.approx(0.0, abs=1e-9)
    assert _dot(pose.down, pose.forward) == pytest.approx(0.0, abs=1e-9)


def test_top_down_camera_looks_along_negative_world_z():
    assert TOP_DOWN.forward == pytest.approx((0.0, 0.0, -1.0), abs=1e-9)
    assert TOP_DOWN.position == pytest.approx((0.0, 0.0, TOP_DOWN_HEIGHT_M))


def test_top_down_camera_puts_world_y_at_the_top_of_the_picture():
    """Down the picture is world -Y, so +Y is up in the image."""
    assert TOP_DOWN.down == pytest.approx((0.0, -1.0, 0.0), abs=1e-9)


def test_look_at_rejects_an_up_hint_along_the_view_direction():
    with pytest.raises(ValueError):
        look_at((0.0, 0.0, 0.4), (0.0, 0.0, 0.0), image_up=(0.0, 0.0, 1.0))


@pytest.mark.parametrize('point', [(0.0, 0.0, 0.0), (0.1, -0.2, 0.05), (-0.3, 0.4, 1.0)])
def test_to_world_and_to_camera_undo_each_other(point):
    pose = look_at((0.14, 0.0, 0.37), (0.0, 0.0, 0.0))
    assert pose.to_camera(pose.to_world(point)) == pytest.approx(point, abs=1e-9)


def test_rotating_a_direction_does_not_move_it():
    """A direction has no position, so the camera's own position must not leak in."""
    pose = look_at((1.0, 2.0, 3.0), (0.0, 0.0, 0.0))
    direction = pose.rotate_to_world((0.0, 0.0, 1.0))
    assert direction == pytest.approx(pose.forward)


def test_rotating_preserves_length():
    pose = look_at((0.14, 0.0, 0.37), (0.0, 0.0, 0.0))
    x, y, z = pose.rotate_to_world((0.3, -0.2, 1.0))
    assert math.sqrt(x * x + y * y + z * z) == pytest.approx(math.sqrt(0.09 + 0.04 + 1.0))


def test_matrix_last_column_is_the_camera_position():
    rows = TOP_DOWN.matrix()
    assert [row[3] for row in rows[:3]] == pytest.approx(list(TOP_DOWN.position))
    assert rows[3] == (0.0, 0.0, 0.0, 1.0)


@pytest.mark.parametrize('eye', [(0.0, 0.0, 0.4), (0.14, 0.0, 0.37), (-0.2, 0.3, 0.9)])
def test_quaternion_is_normalised(eye):
    qx, qy, qz, qw = look_at(eye, (0.0, 0.0, 0.0)).quaternion()
    assert math.sqrt(qx**2 + qy**2 + qz**2 + qw**2) == pytest.approx(1.0)


# -- the scene -------------------------------------------------------------


def test_a_ray_down_the_middle_hits_the_table_at_the_camera_height():
    hit = TABLE_SCENE.trace((0.0, 0.0, TOP_DOWN_HEIGHT_M), (0.0, 0.0, -1.0))
    assert hit is not None
    assert hit.label == 'table'
    assert hit.depth_m == pytest.approx(TOP_DOWN_HEIGHT_M)


def test_a_ray_over_a_box_stops_at_its_top():
    red = TABLE_SCENE.boxes[0]
    origin = (red.centre[0], red.centre[1], TOP_DOWN_HEIGHT_M)
    hit = TABLE_SCENE.trace(origin, (0.0, 0.0, -1.0))
    assert hit is not None
    assert hit.label == 'red'
    assert hit.depth_m == pytest.approx(TOP_DOWN_HEIGHT_M - red.top_z)


def test_a_ray_off_the_table_hits_nothing():
    assert TABLE_SCENE.trace((0.0, 0.0, 0.4), (5.0, 0.0, -1.0)) is None


def test_a_ray_pointing_up_hits_nothing():
    assert TABLE_SCENE.trace((0.0, 0.0, 0.4), (0.0, 0.0, 1.0)) is None


def test_a_box_is_missed_from_beside_it():
    box = Box('one', (200, 0, 0), (0.0, 0.0), (0.04, 0.04, 0.04))
    assert box.intersect((0.5, 0.0, 0.02), (-1.0, 0.0, 0.0)) is not None
    assert box.intersect((0.5, 0.5, 0.02), (-1.0, 0.0, 0.0)) is None


def test_the_nearest_thing_wins():
    """A tall box in front of a short one hides it."""
    tall = Box('tall', (0, 200, 0), (0.0, 0.0), (0.05, 0.05, 0.20))
    scene = Scene(boxes=(tall,))
    hit = scene.trace((0.0, 0.0, 1.0), (0.0, 0.0, -1.0))
    assert hit is not None and hit.label == 'tall'
    assert hit.depth_m == pytest.approx(0.80)


# -- taking a picture ------------------------------------------------------


@pytest.fixture(scope='module')
def shot():
    """One top-down capture through a small lens, shared by the tests below."""
    return capture(TABLE_SCENE, CameraConfig('test', 64, 48, 60.0), TOP_DOWN)


def test_capture_is_the_size_the_config_asked_for(shot):
    assert len(shot.rgb) == 48
    assert all(len(row) == 64 for row in shot.rgb)
    assert len(shot.depth) == 48 and len(shot.labels) == 48


def test_the_table_reads_one_number_from_straight_above(shot):
    """Depth runs along the camera's forward axis, so the corners agree."""
    table_depths = [
        d
        for row, labels in zip(shot.depth, shot.labels)
        for d, label in zip(row, labels)
        if label == 'table' and d is not None
    ]
    assert table_depths
    assert min(table_depths) == pytest.approx(TOP_DOWN_HEIGHT_M)
    assert max(table_depths) == pytest.approx(TOP_DOWN_HEIGHT_M)


def test_each_box_reads_its_own_height_below_the_table(shot):
    for box in TABLE_SCENE.boxes:
        depths = [
            d
            for row, labels in zip(shot.depth, shot.labels)
            for d, label in zip(row, labels)
            if label == box.label and d is not None
        ]
        assert depths, f'{box.label} is not in shot'
        assert min(depths) == pytest.approx(TOP_DOWN_HEIGHT_M - box.top_z)


def test_every_pixel_has_a_depth_reading_here(shot):
    assert shot.valid_depth_fraction() == pytest.approx(1.0)


def test_readings_beyond_the_far_limit_are_dropped():
    near_sighted = CameraConfig('near', 16, 12, 60.0, depth_max_m=0.2)
    clipped = capture(TABLE_SCENE, near_sighted, TOP_DOWN)
    assert clipped.valid_depth_fraction() == 0.0
    assert clipped.depth_range() is None


def test_pixel_to_world_lands_on_the_surface_it_hit(shot):
    """Every deprojected pixel must sit on the thing its label names.

    Not on that thing's *top*: even from straight above, pixels away from the
    middle look outward at a slant, so near the edge of the picture they graze
    the sides of a box. That is the camera behaving correctly, and the check
    below is the one that holds either way.
    """
    boxes = {box.label: box for box in TABLE_SCENE.boxes}
    for row in range(shot.config.height_px):
        for col in range(shot.config.width_px):
            label = shot.labels[row][col]
            point = shot.pixel_to_world(col + 0.5, row + 0.5)
            assert point is not None
            if label == 'table':
                assert point[2] == pytest.approx(0.0, abs=1e-9)
                continue
            bounds = boxes[label].bounds()
            for axis in range(3):
                low, high = bounds[axis]
                assert low - 1e-9 <= point[axis] <= high + 1e-9
            # On a face, not floating inside: one coordinate is at a boundary.
            assert any(
                abs(point[axis] - edge) < 1e-9
                for axis in range(3)
                for edge in bounds[axis]
            )


def test_a_top_down_camera_sees_box_sides_near_the_edges(shot):
    """The reason the test above cannot simply assert the box top height."""
    tops = {box.label: box.top_z for box in TABLE_SCENE.boxes}
    side_hits = 0
    for row in range(shot.config.height_px):
        for col in range(shot.config.width_px):
            label = shot.labels[row][col]
            if label in tops:
                point = shot.pixel_to_world(col + 0.5, row + 0.5)
                if abs(point[2] - tops[label]) > 1e-9:
                    side_hits += 1
    assert side_hits > 0


def test_pixel_to_world_is_none_without_a_depth_reading():
    near_sighted = CameraConfig('near', 8, 6, 60.0, depth_max_m=0.2)
    clipped = capture(TABLE_SCENE, near_sighted, TOP_DOWN)
    assert clipped.pixel_to_world(4.5, 3.5) is None


def test_depth_in_millimetres_is_a_thousand_times_depth_in_metres(shot):
    millimetres = shot.depth_millimetres()
    for row in range(shot.config.height_px):
        for col in range(shot.config.width_px):
            metres = shot.depth[row][col]
            expected = 0 if metres is None else round(metres * 1000.0)
            assert millimetres[row][col] == expected


def test_missing_depth_is_zero_in_millimetres():
    near_sighted = CameraConfig('near', 8, 6, 60.0, depth_max_m=0.2)
    clipped = capture(TABLE_SCENE, near_sighted, TOP_DOWN)
    assert all(value == 0 for row in clipped.depth_millimetres() for value in row)


def test_mono8_is_a_weighted_mix_and_stays_in_range(shot):
    grey = shot.mono8()
    assert all(0 <= value <= 255 for row in grey for value in row)
    r, g, b = shot.rgb[0][0]
    assert grey[0][0] == int(0.299 * r + 0.587 * g + 0.114 * b)


def test_the_mask_picks_out_exactly_one_object(shot):
    mask = shot.mask('red')
    for row in range(shot.config.height_px):
        for col in range(shot.config.width_px):
            assert mask[row][col] == (shot.labels[row][col] == 'red')


def test_point_cloud_has_one_point_per_pixel_with_a_reading(shot):
    assert len(shot.point_cloud()) == shot.config.pixel_count


def test_point_cloud_step_thins_it_out(shot):
    assert len(shot.point_cloud(step=4)) == len(range(0, 48, 4)) * len(range(0, 64, 4))


def test_point_cloud_in_camera_axes_has_depth_as_z(shot):
    for x, y, z, _ in shot.point_cloud(step=8, in_world=False):
        assert z > 0.0
        assert (x, y, z) == pytest.approx(shot.config.deproject(*shot.config.project((x, y, z)), z))


def test_world_points_sit_between_the_table_and_the_tallest_box(shot):
    tallest = max(box.top_z for box in TABLE_SCENE.boxes)
    for _, _, z, _ in shot.point_cloud(step=4):
        assert -1e-9 <= z <= tallest + 1e-9


def test_tilting_the_camera_spreads_the_table_over_a_range_of_depths():
    config = CameraConfig('test', 48, 36, 60.0)
    straight = capture(TABLE_SCENE, config, TOP_DOWN)
    tilted = capture(TABLE_SCENE, config, look_at((0.14, 0.0, 0.37), (0.0, 0.0, 0.0)))
    straight_span = straight.depth_range()
    tilted_span = tilted.depth_range()
    assert tilted_span[1] - tilted_span[0] > straight_span[1] - straight_span[0]


def test_ascii_art_is_the_width_it_was_asked_for(shot):
    lines = shot.ascii_art('rgb', cols=32)
    assert lines and all(len(line) == 32 for line in lines)


# -- the two frame conventions ---------------------------------------------


def _quaternion_multiply(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    )


def _same_rotation(a, b):
    """``q`` and ``-q`` are the same rotation, so accept either."""
    return all(x == pytest.approx(y, abs=1e-9) for x, y in zip(a, b)) or all(
        x == pytest.approx(-y, abs=1e-9) for x, y in zip(a, b)
    )


def test_body_axes_are_forward_left_up():
    forward, left, up = TOP_DOWN.body_axes()
    assert forward == pytest.approx(TOP_DOWN.forward)
    assert left == pytest.approx((-TOP_DOWN.right[0], -TOP_DOWN.right[1], -TOP_DOWN.right[2]))
    assert up == pytest.approx((-TOP_DOWN.down[0], -TOP_DOWN.down[1], -TOP_DOWN.down[2]))


def test_the_standard_static_transform_is_the_turn_between_the_conventions():
    """Optical axes written in body coordinates: right is -Y, down is -Z, forward is +X."""
    derived = axes_to_quaternion((0.0, -1.0, 0.0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0))
    assert _same_rotation(derived, OPTICAL_FROM_BODY_QUATERNION)


@pytest.mark.parametrize(
    'eye', [(0.0, 0.0, 0.4), (0.14, 0.0, 0.37), (0.2, -0.31, 0.55), (-0.1, 0.25, 0.6)]
)
def test_camera_link_then_the_static_turn_lands_on_the_optical_frame(eye):
    """The TF tree the demo publishes must resolve to the frame images are stamped in."""
    pose = look_at(eye, (0.0, 0.0, 0.0))
    chained = _quaternion_multiply(pose.body_quaternion(), OPTICAL_FROM_BODY_QUATERNION)
    assert _same_rotation(chained, pose.quaternion())


@pytest.mark.parametrize('box', TABLE_SCENE.boxes, ids=lambda b: b.label)
def test_measuring_a_box_finds_where_it_stands_and_how_tall(box):
    """The problem the doc opens with: position and height, from pixels alone."""
    x, y, height = capture(TABLE_SCENE, WRIST, TOP_DOWN).measure(box.label)
    assert math.hypot(x - box.centre[0], y - box.centre[1]) < 0.001
    assert height == pytest.approx(box.top_z, abs=0.001)


def test_measuring_something_not_in_shot_gives_nothing():
    assert capture(TABLE_SCENE, WRIST, TOP_DOWN).measure('purple') is None
