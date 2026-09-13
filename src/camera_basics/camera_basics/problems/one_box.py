"""Part 1: one box. Every idea about a camera, on the simplest case.

Run it:  make camera.learn   (or: ros2 run camera_basics camera_one_box)

Only the red box is on the table: a 6 cm cube, 40 cm below a camera looking
straight down. This part uses a basic camera, only 80 x 60 pixels, so that
every pixel it returns can be drawn and looked at. It walks through what that
camera makes of the box, from the four numbers that describe its lens to the
box measured in the room. The last step measures the box again with the doc's
bigger 320 x 240 camera, to show what more pixels buy. Part 2, three_boxes.py,
puts the other two boxes back.

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
    ONE_BOX_SCENE,
    Scene,
    TOP_DOWN,
    WRIST,
)

#: The basic camera this part uses: the same 60 degree lens as the doc's camera,
#: but only 80 x 60 pixels. That is 4,800 pixels, few enough to draw every one.
BASIC = CameraConfig('basic', 80, 60, 60.0)

#: A pixel picked out below, in the basic camera's picture: on top of the red
#: box, off centre so that both halves of the arithmetic have work to do.
SAMPLE_PIXEL = (53.5, 21.5)

#: A small patch of the picture, as (first column, last column, first row, last
#: row). It sits on the box's left edge, so it holds table, side and top.
PATCH = (43, 50, 19, 23)

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


def draw_pixels(colours) -> None:
    """Print a picture in the terminal, one coloured square for every pixel.

    Each character on screen holds two pixels, one above the other. The top
    pixel is the colour of the half block '▀' itself, and the bottom pixel is
    the colour behind it. Terminal characters are about twice as tall as they
    are wide, so this makes every pixel come out square.

    The colours use the standard 24-bit colour codes, which almost every modern
    terminal understands.
    """
    rows = list(colours)
    if len(rows) % 2:
        rows.append([(0, 0, 0)] * len(rows[0]))    # an odd last row gets a black partner
    for top, bottom in zip(rows[0::2], rows[1::2]):
        line = ''.join(
            f'\x1b[38;2;{r1};{g1};{b1}m\x1b[48;2;{r2};{g2};{b2}m▀'
            for (r1, g1, b1), (r2, g2, b2) in zip(top, bottom)
        )
        print('  ' + line + '\x1b[0m')


def depth_to_grey(shot: Capture) -> list[list[tuple[int, int, int]]]:
    """Turn each depth reading into a shade of grey: the nearer, the brighter.

    The furthest reading in the picture becomes dark grey and the nearest
    becomes white. A pixel with no reading would be black.
    """
    near, far = shot.depth_range()
    spread = (far - near) or 1.0
    pixels = []
    for row in shot.depth:
        line = []
        for depth_m in row:
            if depth_m is None:
                line.append((0, 0, 0))
                continue
            level = round(60 + 195 * (far - depth_m) / spread)
            line.append((level, level, level))
        pixels.append(line)
    return pixels


def show_lens(config: CameraConfig = BASIC) -> None:
    """Print the four lens numbers of the camera this part uses."""
    heading('the lens: four numbers, and where they come from')
    print(f'The camera is {config.width_px} x {config.height_px} pixels and sees '
          f'{config.hfov_deg:g}° across.')
    print('Those two facts decide all four numbers that describe its lens.\n')
    print(f'  fx = fy = {config.fx:.1f}   the focal length, counted in pixels')
    print(f'  cx      = {config.cx:g}     the middle of the picture, across')
    print(f'  cy      = {config.cy:g}     the middle of the picture, down')
    print(
        f'\nCheck fx by hand: half the width, divided by tan of half the field of'
        f'\nview, is {config.width_px // 2} / tan({config.hfov_deg / 2:g}°) = {config.fx:.1f}. '
        f'The picture is only {config.height_px} pixels'
        f'\ntall, so the same focal length sees {config.vfov_deg:.1f}° down it.'
    )


def show_coverage(config: CameraConfig = BASIC, distance_m: float = 0.40) -> None:
    """Print how much of the table the camera sees, and how finely."""
    heading(f'what that buys you, {distance_m:g} m from the table')
    width_m, height_m = config.coverage_m(distance_m)
    print(f'From {distance_m:g} m up, the picture covers {width_m:.3f} m x {height_m:.3f} m '
          'of the table.')
    print(f'Its {config.pixel_count:,} pixels cut that into squares of '
          f'{config.metres_per_pixel(distance_m) * 1000:.2f} mm, so nothing much')
    print('smaller than that can be measured from this height. Section 1.7 of the')
    print('doc compares this with other lenses and other resolutions.')


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


def show_colour_picture(shot: Capture) -> None:
    """Draw the colour picture exactly as the camera returned it."""
    heading('the colour picture, every pixel')
    config = shot.config
    print(f'This is exactly what the camera returned: {config.width_px} pixels across and '
          f'{config.height_px} down,')
    print('each one a single colour. Nothing is smoothed or left out. The grey')
    print('squares are the table, with its 5 cm grid, and the red block is the box.\n')
    draw_pixels(shot.rgb)


def show_depth_picture(shot: Capture) -> None:
    """Draw the depth picture, one grey square per reading."""
    heading('the depth picture, every pixel')
    near, far = shot.depth_range()
    print('The same pixels again, but each one now holds a distance instead of a')
    print(f'colour. Nearer is brighter: {far:.3f} m is dark grey and {near:.3f} m is '
          'white. The')
    print('box stands out because its top is nearer the camera than the table.\n')
    draw_pixels(depth_to_grey(shot))


def show_pixel_numbers(shot: Capture) -> None:
    """Print the actual numbers behind a small patch of pixels."""
    heading('the numbers behind the pixels')
    first_col, last_col, first_row, last_row = PATCH
    print('A picture is only numbers. Here are the depth readings, in metres, for')
    print(f'columns {first_col} to {last_col} and rows {first_row} to {last_row}, '
          "on the box's left edge:\n")
    print('         ' + ''.join(f'{col:>7}' for col in range(first_col, last_col + 1)))
    for row in range(first_row, last_row + 1):
        readings = shot.depth[row][first_col:last_col + 1]
        print(f'  row {row:<3}' + ''.join(f'{d:>7.3f}' for d in readings))
    table, side, top = (shot.rgb[first_row][col]
                        for col in (first_col, first_col + 3, first_col + 4))
    print(
        '\nThe table reads 0.400, the top of the box reads 0.340, and the one'
        '\ncolumn in between is the side of the box, which the camera catches'
        '\nat an angle. The colour picture holds three numbers in each pixel'
        f'\ninstead, for red, green and blue:\n'
        f'\n  {table} on the table'
        f'\n  {side} on the side, in shadow'
        f'\n  {top} on the top'
    )


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
    x_line = (f'  x = (u - cx) * depth / fx = ({u:g} - {config.cx:g})'
              f' * {depth_m:.3f} / {config.fx:.1f} = ')
    y_line = (f'  y = (v - cy) * depth / fy = ({v:g} - {config.cy:g})'
              f' * {depth_m:.3f} / {config.fy:.1f} = ')
    width = max(len(x_line), len(y_line))
    print(f'{x_line:>{width}}{x:+.4f} m')
    print(f'{y_line:>{width}}{y:+.4f} m')
    print(f"{'  z =  depth':<{width - 2}}= {z:+.4f} m")
    wx, wy, wz = shot.pixel_to_world(u, v)
    print(f'\nMoved into the room by camera_to_world: ({wx:+.4f}, {wy:+.4f}, {wz:+.4f})')
    print(f'The red box top is {scene.boxes[0].top_z:.3f} m above the table, and z agrees.')

    back = config.project((x, y, z))
    print(f'\nProject it again and the pixel comes back: ({back[0]:.1f}, {back[1]:.1f}).')
    print('Round trip, because the two formulas are one formula read both ways.')

    heading('every pixel at once is a point cloud')
    cloud = shot.point_cloud()
    print(f'Every pixel, deprojected: {len(cloud):,} points.')
    print('The picture was a grid of directions; this is a bag of places.\n')

    # One point off each thing in the scene, rather than five off the table.
    first: dict[str, tuple[float, float, float]] = {}
    for row in range(config.height_px):
        for col in range(config.width_px):
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
    print('\nWithin a millimetre or so, and the height exact, from one picture.')


def show_more_pixels(scene: Scene) -> None:
    """Measure the box with the basic camera and with the doc's camera, side by side."""
    heading("more pixels: the same box through the doc's camera")
    print(f'The doc uses a camera with the same lens but {WRIST.width_px} x {WRIST.height_px} '
          'pixels, sixteen')
    print('times as many. Each of its pixels is a quarter as wide, so it finds the')
    print('edges of the box more precisely.\n')
    print(f"{'camera':<12}{'pixels':>8}{'one pixel':>12}{'measured middle':>21}{'height':>9}")
    print('-' * 62)
    for config in (BASIC, WRIST):
        x, y, height = capture(scene, config, TOP_DOWN).measure('red')
        size = f'{config.width_px} x {config.height_px}'
        print(f'{size:<12}{config.pixel_count:>8,}'
              f'{config.metres_per_pixel(0.40) * 1000:>9.2f} mm'
              f'    ({x:+.3f}, {y:+.3f}){height:>9.3f}')
    true_x, true_y = scene.boxes[0].centre
    print(f"{'the truth':<12}{'':>8}{'':>12}    ({true_x:+.3f}, {true_y:+.3f})"
          f'{scene.boxes[0].top_z:>9.3f}')
    print('\nThe height is exact either way, because every reading on the top is')
    print('the same. The middle gets closer to the truth with more pixels.')


def main() -> None:
    """Print part 1: every idea, on one box."""
    print(__doc__.split('THE IDEA')[0].strip())
    start_numbering()

    show_lens()
    show_coverage()
    show_pose()

    shot = capture(ONE_BOX_SCENE, BASIC, TOP_DOWN)
    show_colour_picture(shot)
    show_depth_picture(shot)
    show_pixel_numbers(shot)
    show_depth_numbers(shot, ONE_BOX_SCENE)
    show_pixel_to_point(shot, ONE_BOX_SCENE)
    show_encodings(shot)
    show_measurements(shot, ONE_BOX_SCENE)
    show_more_pixels(ONE_BOX_SCENE)

    print('\nNext: three_boxes.py puts the other two boxes back.')


if __name__ == '__main__':
    main()
