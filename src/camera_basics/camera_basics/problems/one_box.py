"""Part 1: one box. Every idea about a camera, on the simplest case.

Run it:  make camera.learn   (or: ros2 run camera_basics camera_one_box)

Only the red box is on the table: a 6 cm cube, 40 cm below a camera looking
straight down. This walks through what the camera makes of it, from the four
numbers that describe the lens to the box measured in the room. Part 2,
three_boxes.py, puts the other two boxes back.

THE IDEA
--------
A picture is a grid of pixels, and each pixel is a direction, not a place: the
distance to whatever it saw has been thrown away. A depth picture puts that
distance back, one reading per pixel. A direction plus a distance is a point.

With one box, finding its pixels is easy: anything that reads nearer than the
table is the box. Turn those pixels into points in the room, keep the top, and
average it. That says where the box is and how tall it is.

The camera itself (lens, pose, scene, capture) is in ``camera.py``. This file
only drives it and prints what comes out.
"""

from camera_basics.camera import (
    CameraConfig,
    Capture,
    capture,
    CONFIGS,
    field_of_view_deg,
    ONE_BOX_SCENE,
    Scene,
    TOP_DOWN,
    WRIST,
)

#: Small enough to render several times in a couple of seconds, and big enough
#: that the terminal pictures below are recognisable.
PREVIEW = CameraConfig('preview', 160, 120, 60.0)

#: A pixel picked out below: on top of the red box, off centre so that both
#: halves of the arithmetic have work to do.
SAMPLE_PIXEL = (212.5, 86.5)

_SECTION = [0]


def start_numbering() -> None:
    """Restart section numbering at 1. Each part numbers its own sections."""
    _SECTION[0] = 0


def heading(text: str) -> None:
    """Print a section heading, numbered in the order the sections run."""
    _SECTION[0] += 1
    print(f'\n--- {_SECTION[0]}. {text} ---\n')


def side_by_side(left: list[str], right: list[str], gap: str = '   ') -> list[str]:
    """Put two terminal pictures next to each other, line by line."""
    width = max((len(line) for line in left), default=0)
    height = max(len(left), len(right))
    rows = []
    for i in range(height):
        a = left[i] if i < len(left) else ''
        b = right[i] if i < len(right) else ''
        rows.append(f'{a:<{width}}{gap}{b}')
    return rows


def show_lenses() -> None:
    """Print the four lens numbers for each configuration."""
    heading('the lens: four numbers, and where they come from')
    print('Change the field of view and the focal length changes with it.')
    print('Change the resolution and the middle of the picture moves.\n')
    print(f"{'name':<10} {'size':^9} {'hfov':>6} {'vfov':>6} {'fx=fy':>7} {'cx':>6} {'cy':>6}")
    print('-' * 55)
    for config in CONFIGS.values():
        print(config.describe())
    print(
        f'\nCheck one by hand: {WRIST.name} is {WRIST.width_px} px across '
        f'{WRIST.hfov_deg:g}°,\nso fx = {WRIST.width_px // 2} / tan(30°) = '
        f'{WRIST.fx:.1f}. Read it back with the inverse and\nthe field of view '
        f'comes out at {field_of_view_deg(WRIST.width_px, WRIST.fx):.1f}° again.'
    )


def show_coverage(distance_m: float = 0.40) -> None:
    """Print how much of the table each lens sees, and how finely."""
    heading(f'what that buys you, {distance_m:g} m from the table')
    print('Field of view decides how much is in shot. Resolution decides how')
    print('finely it is sampled. They are separate knobs, and this is the proof:')
    print('wide and narrow see different amounts at the same resolution, while')
    print('hires and lowres see the same amount at different sharpness.\n')
    print(f"{'name':<10} {'sees (w x h)':>18} {'per pixel':>12} {'pixels':>10}")
    print('-' * 54)
    for config in CONFIGS.values():
        width_m, height_m = config.coverage_m(distance_m)
        print(
            f'{config.name:<10} {width_m:>8.3f} x {height_m:<7.3f} '
            f'{config.metres_per_pixel(distance_m) * 1000:>8.2f} mm '
            f'{config.pixel_count:>10,}'
        )


def show_pose() -> None:
    """Print where the camera is, as camera_to_world."""
    heading('where the camera is: camera_to_world')
    print('The picture says "0.34 m in front of me". Where that is depends on')
    print('where "me" was, so every capture carries this alongside it.\n')
    labels = ('right (+X)', 'down (+Y)', 'forward (+Z)', 'position')
    print(f"{'':<8}" + ''.join(f'{name:>14}' for name in labels))
    for axis, row in zip(('world x', 'world y', 'world z', ''), TOP_DOWN.matrix()):
        print(f'{axis:<8}' + ''.join(f'{value + 0.0:>14.3f}' for value in row))
    print(
        '\nRead the columns as directions. This camera looks along world -Z,'
        '\nstraight down, from 0.40 m up. Its "down the picture" is world -Y,'
        '\nwhich is to say world +Y comes out at the top of the picture.'
    )
    qx, qy, qz, qw = TOP_DOWN.quaternion()
    print(
        '\nSame rotation as ROS stores it: '
        f'({qx + 0.0:.3f}, {qy + 0.0:.3f}, {qz + 0.0:.3f}, {qw + 0.0:.3f})'
    )


def show_captures(shot: Capture) -> None:
    """Print one capture as two terminal pictures: colour and depth."""
    heading('one capture, two pictures')
    print('The same pixels twice. Colour on the left, depth on the right:')
    print('denser characters are nearer, so anything taller than the table')
    print('stands out of it.\n')
    for line in side_by_side(shot.ascii_art('rgb', 40), shot.ascii_art('depth', 40)):
        print('  ' + line)


def show_depth_numbers(shot: Capture, scene: Scene) -> None:
    """Print how many depth readings land on each thing, and what they read."""
    heading('where the depth readings land')
    total = shot.config.pixel_count
    valid = round(shot.valid_depth_fraction() * total)
    print(f'One reading per pixel: {total:,} of them, and {valid:,} came back with a number.')
    span = shot.depth_range()
    print(f'They run from {span[0]:.3f} m to {span[1]:.3f} m.\n')
    counts: dict[str, int] = {}
    for labels in shot.labels:
        for label in labels:
            counts[label] = counts.get(label, 0) + 1
    print(f"{'landed on':<10} {'readings':>9} {'top reads':>11} {'height above the table':>24}")
    print('-' * 57)
    table_depth = max(
        d for row, labels in zip(shot.depth, shot.labels)
        for d, label in zip(row, labels) if d is not None and label == 'table'
    )
    print(f"{'table':<10} {counts.get('table', 0):>9,} {table_depth:>9.3f} m {'—':>23}")
    for box in scene.boxes:
        tops = [
            d for row, labels in zip(shot.depth, shot.labels)
            for d, label in zip(row, labels) if d is not None and label == box.label
        ]
        nearest = min(tops)
        print(f'{box.label:<10} {counts.get(box.label, 0):>9,} {nearest:>9.3f} m'
              f' {table_depth - nearest:>21.3f} m')
    print(
        f'\nThe table reads {table_depth:.2f} m everywhere, corners included,'
        '\nbecause depth is measured along the way the camera looks and not'
        '\nalong the slanted line to each point. Subtract and you have the'
        '\nheight of each box, to the millimetre, from one picture.'
    )


def show_pixel_to_point(shot: Capture, scene: Scene) -> None:
    """Work one pixel through to a point, then show a point cloud."""
    heading('a pixel becomes a point')
    u, v = SAMPLE_PIXEL
    config = shot.config
    depth_m = shot.depth_at(u, v)
    print(f'Take pixel ({u:g}, {v:g}). It landed on the {shot.label_at(u, v)} box.')
    print(f'Its depth reading is {depth_m:.3f} m.\n')
    x, y, z = config.deproject(u, v, depth_m)
    print('Measured from the camera, undoing the divide-by-depth:')
    print(f'  x = (u - cx) * depth / fx = ({u:g} - {config.cx:g})'
          f' * {depth_m:.3f} / {config.fx:.1f} = {x:+.4f} m')
    print(f'  y = (v - cy) * depth / fy = ({v:g} - {config.cy:g})'
          f' * {depth_m:.3f} / {config.fy:.1f} = {y:+.4f} m')
    print(f'  z =  depth                                          = {z:+.4f} m')
    wx, wy, wz = shot.pixel_to_world(u, v)
    print(f'\nMoved into the room by camera_to_world: ({wx:+.4f}, {wy:+.4f}, {wz:+.4f})')
    print(f'The red box top is {scene.boxes[0].top_z:.3f} m above the table, and z agrees.')

    back = config.project((x, y, z))
    print(f'\nProject it again and the pixel comes back: ({back[0]:.1f}, {back[1]:.1f}).')
    print('Round trip, because the two formulas are one formula read both ways.')

    heading('every pixel at once is a point cloud')
    cloud = shot.point_cloud(step=4)
    print(f'One in sixteen pixels, deprojected: {len(cloud):,} points.')
    print('The picture was a grid of directions; this is a bag of places.\n')

    # One point off each thing in the scene, rather than five off the table.
    first: dict[str, tuple[float, float, float]] = {}
    for row in range(0, config.height_px, 4):
        for col in range(0, config.width_px, 4):
            label = shot.labels[row][col]
            if label is not None and label not in first:
                point = shot.pixel_to_world(col + 0.5, row + 0.5)
                if point is not None:
                    first[label] = point
    print(f"{'landed on':<10} {'x':>9} {'y':>9} {'z':>9}")
    print('-' * 40)
    for label, (x, y, z) in first.items():
        print(f'{label:<10} {x:>9.3f} {y:>9.3f} {z:>9.3f}')
    print(
        '\nEvery z is the height of the thing that pixel landed on: 0 for the'
        '\ntable, and each box top at its own height. Nothing measured that.'
        '\nIt fell out of one depth reading per pixel and the arithmetic above.'
    )


def show_encodings(shot: Capture) -> None:
    """Print the same shot in each encoding ROS uses."""
    heading('the same shot in the encodings ROS uses')
    u, v = SAMPLE_PIXEL
    row, col = int(v), int(u)
    config = shot.config
    mono = shot.mono8()
    depth_mm = shot.depth_millimetres()
    print(f"{'encoding':<10} {'per pixel':<22} {'bytes':>10}   at the sample pixel")
    print('-' * 78)
    print(f"{'rgb8':<10} {'3 bytes: r, g, b':<22} {config.pixel_count * 3:>10,}"
          f'   {shot.rgb_at(u, v)}')
    print(f"{'mono8':<10} {'1 byte: brightness':<22} {config.pixel_count:>10,}"
          f'   {mono[row][col]}')
    print(f"{'32FC1':<10} {'4 bytes: metres':<22} {config.pixel_count * 4:>10,}"
          f'   {shot.depth_at(u, v):.4f} m')
    print(f"{'16UC1':<10} {'2 bytes: millimetres':<22} {config.pixel_count * 2:>10,}"
          f'   {depth_mm[row][col]} mm')
    print(
        '\nThe last two are the same measurement in different clothes, and'
        '\nmixing them up is a thousand-fold error. They disagree about how to'
        '\nsay "no reading" too: 32FC1 uses NaN, 16UC1 uses 0.'
    )
    red_pixels = sum(1 for row_mask in shot.mask('red') for cell in row_mask if cell)
    print(f'\nAnd the mask: {red_pixels:,} pixels belong to the red box.')


def show_lens_comparison(scene: Scene) -> None:
    """Take the same shot through three lenses and draw each."""
    heading('change the lens, keep everything else')
    print(f'Same scene, same place, all three {PREVIEW.width_px} px across. Only the')
    print('field of view differs, and the 5 cm grid on the table shows the cost.\n')
    for name in ('wide', 'wrist', 'narrow'):
        config = CameraConfig(name, PREVIEW.width_px, PREVIEW.height_px, CONFIGS[name].hfov_deg)
        shot = capture(scene, config, TOP_DOWN)
        width_m, _ = config.coverage_m(0.40)
        print(f'  {name}  —  {config.hfov_deg:g}° across, {width_m:.3f} m of table, '
              f'{config.metres_per_pixel(0.40) * 1000:.1f} mm per pixel')
        for line in shot.ascii_art('rgb', 34):
            print('    ' + line)
        print()
    print('Wide fits more in and spends fewer pixels on each thing. Narrow')
    print('spends more pixels on less. Neither is sharper than the other: the')
    print('sensor did not change, only what was aimed at it.')


def show_measurements(shot: Capture, scene: Scene) -> None:
    """Measure every box in the scene and compare with the truth."""
    heading('the answer: measured, next to the truth')
    print('Each box from its own pixels only: deproject them, keep its top,')
    print('and average. Then compare with the true sizes the scene was built with.\n')
    print(f"{'box':<7}{'measured middle':>18}{'true middle':>18}{'height':>9}{'true':>7}")
    print('-' * 59)
    for box in scene.boxes:
        x, y, height = shot.measure(box.label)
        true_x, true_y = box.centre
        print(f'{box.label:<7}  ({x:+.3f}, {y:+.3f})   ({true_x:+.3f}, {true_y:+.3f})'
              f'{height:>9.3f}{box.top_z:>7.3f}')
    print('\nWithin a millimetre, and the height exact, from one picture.')


def main() -> None:
    """Print part 1: every idea, on one box."""
    print(__doc__.split('THE IDEA')[0].strip())
    start_numbering()

    show_lenses()
    show_coverage()
    show_pose()

    shot = capture(ONE_BOX_SCENE, WRIST, TOP_DOWN)
    show_captures(capture(ONE_BOX_SCENE, PREVIEW, TOP_DOWN))
    show_depth_numbers(shot, ONE_BOX_SCENE)
    show_pixel_to_point(shot, ONE_BOX_SCENE)
    show_encodings(shot)
    show_lens_comparison(ONE_BOX_SCENE)
    show_measurements(shot, ONE_BOX_SCENE)

    print('\nNext: three_boxes.py puts the other two boxes back.')


if __name__ == '__main__':
    main()
