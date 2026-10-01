"""Turn the object's pixel into a position in metres, using the depth picture.

find_by_colour.py says which pixel the object is on. A pixel on its own is only
a direction: everything along that line lands on the same pixel, whether it is
5 cm or 5 m away. A depth camera fills in the missing number. For every pixel it
also reports how far ahead the surface is, in metres, and with that the pixel
becomes a point.

This file does the three things every robot does with a depth picture:

  1. read the depth of the object, safely: the median of its pixels, skipping
     the ones the camera could not measure
  2. turn pixel plus depth into x, y, z in metres, with the lens numbers
  3. measure the object: how wide it is, and how tall it stands above the table

The data is one frame recorded from the camera area's Gazebo simulation, in
data/: the colour picture, the depth picture as a NumPy file, and the lens
numbers as JSON. The camera basics doc explains where those numbers come from.

Run it with:  pixi run python src/camera/camera_basics/depth_of_object.py
"""

from dataclasses import dataclass
import json
import pathlib

from find_by_colour import colour_mask, Found, largest_object, load_picture, tidy
import numpy as np
from numpy.typing import NDArray

HERE: pathlib.Path = pathlib.Path(__file__).resolve().parent
PICTURE: pathlib.Path = HERE / 'data' / 'table_colour.png'
DEPTH: pathlib.Path = HERE / 'data' / 'table_depth.npz'
CAMERA: pathlib.Path = HERE / 'data' / 'table_camera.json'


@dataclass(frozen=True)
class Lens:
    """The four numbers that describe a camera's lens, in pixels."""

    fx: float                 # how many pixels one radian covers, across
    fy: float                 # and down
    cx: float                 # the middle of the picture, across
    cy: float                 # and down


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def load_depth(path: pathlib.Path) -> NDArray[np.float32]:
    """Read the depth picture: one distance in metres for every pixel.

    A real program gets this from the camera driver, as a sensor_msgs/Image with
    encoding 32FC1, and turns it into exactly this array with cv_bridge. Here it
    is kept in a NumPy file so that this folder needs no ROS.
    """
    depth: NDArray[np.float32] = np.load(path)['depth']
    return depth


def load_lens(path: pathlib.Path) -> Lens:
    """Read the lens numbers, which a real program reads from a CameraInfo message."""
    numbers: dict[str, float] = json.load(path.open())
    return Lens(fx=numbers['fx'], fy=numbers['fy'], cx=numbers['cx'], cy=numbers['cy'])


def depth_of(depth: NDArray[np.float32], mask: NDArray[np.uint8]) -> float:
    """Say how far away the masked object is, in metres.

    Two things make this more than "read one pixel". A depth camera leaves
    pixels it could not measure as NaN, "not a number", so those are dropped.
    And one wrong reading at the edge of the object, where the beam half hits
    the table behind it, would spoil an average, so this takes the median: the
    middle reading when they are sorted.
    """
    readings: NDArray[np.float32] = depth[(mask > 0) & np.isfinite(depth)]
    if readings.size == 0:
        raise ValueError('the camera measured none of the object')
    return float(np.median(readings))


def pixel_to_point(u: float, v: float, z: float, lens: Lens) -> tuple[float, float, float]:
    """Turn a pixel and its depth into a point in metres, measured from the camera.

    This is the whole of a depth camera in two lines. (u - cx) is how many
    pixels right of the middle the object is, and dividing by fx turns pixels
    into an angle, near enough, so multiplying by the depth gives metres. The
    camera's own axes are x to the right, y down and z straight ahead.
    """
    x: float = (u - lens.cx) * z / lens.fx
    y: float = (v - lens.cy) * z / lens.fy
    return x, y, z


def size_in_metres(pixels: float, z: float, focal_length: float) -> float:
    """Turn a size in pixels, at this depth, into a size in metres."""
    return pixels * z / focal_length


def main() -> None:
    """Find the box by colour, then measure where it is and how big it is."""
    bgr: NDArray[np.uint8] = load_picture(PICTURE)
    mask: NDArray[np.uint8] = tidy(colour_mask(bgr))
    found: Found | None = largest_object(mask)
    depth: NDArray[np.float32] = load_depth(DEPTH)
    lens: Lens = load_lens(CAMERA)
    if found is None:
        print('nothing of that colour in this picture')
        return

    heading('1. The lens, and the depth picture')
    print(f'lens: fx = {lens.fx:.1f}, fy = {lens.fy:.1f}, '
          f'cx = {lens.cx:.1f}, cy = {lens.cy:.1f}  (pixels)')
    print(f'depth picture: {depth.shape[1]} x {depth.shape[0]} readings, {depth.dtype}, '
          f'in metres')
    print(f'nearest reading {np.nanmin(depth):.3f} m, farthest {np.nanmax(depth):.3f} m, '
          f'{int(np.isnan(depth).sum())} missing')

    heading('2. How far away the object is')
    z: float = depth_of(depth, mask)
    print(f'the object, over {int((mask > 0).sum()):,} pixels: {z:.3f} m')
    # The table is whatever the camera sees where the object is not. The corner
    # pixels are table in this picture, and a robot usually knows its table
    # anyway, from the transform that says where the camera is above it.
    table: float = float(np.nanmedian(depth[~(mask > 0)]))
    print(f'the table, everywhere else:          {table:.3f} m')

    heading('3. Where the object is, in metres')
    x: float
    y: float
    x, y, z = pixel_to_point(found.u, found.v, z, lens)
    print(f'pixel ({found.u:.1f}, {found.v:.1f}) at {z:.3f} m '
          f'-> x = {x:+.3f} m, y = {y:+.3f} m, z = {z:.3f} m')
    print('measured from the camera: x to its right, y down, z straight ahead.')
    print('The camera looks straight down here, so x and y run along the table')
    print('and z is the height of the camera above what it sees.')

    heading('4. How big the object is')
    across: float = size_in_metres(found.width, z, lens.fx)
    down: float = size_in_metres(found.height, z, lens.fy)
    print(f'bounding box {found.width} x {found.height} pixels at {z:.3f} m '
          f'-> {across * 100:.1f} x {down * 100:.1f} cm')
    print(f'it stands {(table - z) * 100:.1f} cm above the table '
          f'({table:.3f} - {z:.3f} m)')


if __name__ == '__main__':
    main()
