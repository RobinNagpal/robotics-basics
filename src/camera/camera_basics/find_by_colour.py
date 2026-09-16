"""Find an object in a picture by its colour, with OpenCV.

This is the oldest and simplest way a robot finds something, and it is still
used every day: a coloured ball, a coloured marker on a tool, a red emergency
button, a green crop against brown soil. It needs no model and no training, and
it runs in a millisecond. It only works when the object's colour is not shared
by anything else in view.

The steps are always the same, and they are the steps in this file:

  1. read the picture
  2. convert it from colours to hue, saturation and value (HSV)
  3. keep the pixels whose hue is the one you want: a mask
  4. tidy the mask up
  5. find the blobs in the mask, and take the biggest one
  6. say where its middle is

The picture is data/table_colour.png, one frame recorded from the camera area's
Gazebo simulation: a camera 0.40 m above a table, looking down at a red box.

Run it with:  pixi run python src/camera/camera_basics/find_by_colour.py
"""

from collections.abc import Sequence
from dataclasses import dataclass
import pathlib

import cv2
import numpy as np
from numpy.typing import NDArray

HERE: pathlib.Path = pathlib.Path(__file__).resolve().parent
PICTURE: pathlib.Path = HERE / 'data' / 'table_colour.png'
OUT: pathlib.Path = HERE / 'out'

# The colour to look for, as hue, saturation and value. OpenCV keeps hue in
# 0..179 (half of the usual 0..360 degrees), and saturation and value in 0..255.
# Red sits at both ends of the hue circle, so it needs two ranges. The box in
# this picture has hue 3 and saturation about 120; the table is grey, which
# means saturation 0, so "saturation above 80" alone separates them.
LOW_RED: NDArray[np.uint8] = np.array([0, 80, 40], dtype=np.uint8)
HIGH_RED: NDArray[np.uint8] = np.array([10, 255, 255], dtype=np.uint8)
LOW_RED_WRAPPED: NDArray[np.uint8] = np.array([170, 80, 40], dtype=np.uint8)
HIGH_RED_WRAPPED: NDArray[np.uint8] = np.array([179, 255, 255], dtype=np.uint8)

# Blobs smaller than this many pixels are noise, not the object.
MIN_PIXELS: int = 100


@dataclass(frozen=True)
class Found:
    """Where an object is in a picture, in pixels."""

    u: float                  # the middle, across the picture
    v: float                  # the middle, down the picture
    left: int                 # the bounding box: the smallest box round the blob
    top: int
    width: int
    height: int
    pixels: int               # how many pixels the blob covers


def heading(text: str) -> None:
    """Print a section title, so the output reads in the same order as the file."""
    print(f'\n--- {text} ---')


def as_picture(result: cv2.typing.MatLike) -> NDArray[np.uint8]:
    """Say that what OpenCV handed back is a picture: an array of bytes.

    OpenCV's Python type information calls everything it returns a "MatLike",
    which covers several kinds of matrix it can use inside. Robot code keeps
    pictures as NumPy arrays of bytes, and this says so. Nothing is copied.
    """
    return np.asarray(result, dtype=np.uint8)


def load_picture(path: pathlib.Path) -> NDArray[np.uint8]:
    """Read a picture from a file, as an array of pixels.

    cv2.imread gives the three colours of each pixel in the order blue, green,
    red, not red, green, blue. That is an old OpenCV habit, and it is the most
    common bug in first vision programs: get it wrong and red and blue swap.
    """
    picture: cv2.typing.MatLike | None = cv2.imread(str(path))
    if picture is None:
        raise FileNotFoundError(f'no picture at {path}')
    return as_picture(picture)


def colour_mask(bgr: NDArray[np.uint8]) -> NDArray[np.uint8]:
    """Mark every pixel of the colour we are looking for.

    The picture is converted to HSV first: hue (which colour it is), saturation
    (how strong the colour is) and value (how bright it is). This is done
    because hue hardly changes when the light does, while the red, green and
    blue numbers all change together. A red object in shadow is still hue 3; it
    is only darker, which moves value, not hue. That is why robot code
    thresholds in HSV and not in RGB.

    The result is a mask: 255 where the pixel matches, 0 where it does not.
    """
    hsv: NDArray[np.uint8] = as_picture(cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV))
    mask: NDArray[np.uint8] = as_picture(cv2.inRange(hsv, LOW_RED, HIGH_RED))
    wrapped: NDArray[np.uint8] = as_picture(cv2.inRange(hsv, LOW_RED_WRAPPED, HIGH_RED_WRAPPED))
    return as_picture(cv2.bitwise_or(mask, wrapped))


def tidy(mask: NDArray[np.uint8]) -> NDArray[np.uint8]:
    """Remove specks, and fill small holes.

    A real camera's mask is never clean: single pixels flicker on, and a
    highlight leaves a hole in the middle of the object. "Opening" (shrink then
    grow) removes specks smaller than the brush, and "closing" (grow then
    shrink) fills holes smaller than it. The brush is the 5 x 5 square below.
    """
    brush: NDArray[np.uint8] = as_picture(
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    opened: NDArray[np.uint8] = as_picture(cv2.morphologyEx(mask, cv2.MORPH_OPEN, brush))
    return as_picture(cv2.morphologyEx(opened, cv2.MORPH_CLOSE, brush))


def largest_object(mask: NDArray[np.uint8]) -> Found | None:
    """Find the blobs in the mask, and describe the biggest one.

    cv2.findContours traces the outline of every blob. RETR_EXTERNAL keeps only
    the outer outlines, so a hole inside the object is not a second blob, and
    CHAIN_APPROX_SIMPLE stores the corners of each outline instead of every
    pixel along it.
    """
    contours: Sequence[cv2.typing.MatLike]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    biggest: cv2.typing.MatLike = max(contours, key=cv2.contourArea)
    pixels: int = int(cv2.contourArea(biggest))
    if pixels < MIN_PIXELS:
        return None

    # The bounding box: the smallest upright box round the blob.
    left: int
    top: int
    width: int
    height: int
    left, top, width, height = cv2.boundingRect(biggest)

    # The middle, from the blob's "moments". m00 is its area, m10 is the sum of
    # every pixel's column number and m01 the sum of every row number, so
    # m10 / m00 and m01 / m00 are the average column and row: the middle of the
    # shape. It is steadier than the middle of the bounding box, because one
    # stray pixel at the edge moves the box but hardly moves the average.
    moments: dict[str, float] = cv2.moments(biggest)
    return Found(u=moments['m10'] / moments['m00'], v=moments['m01'] / moments['m00'],
                 left=left, top=top, width=width, height=height, pixels=pixels)


def annotate(bgr: NDArray[np.uint8], found: Found) -> NDArray[np.uint8]:
    """Draw the bounding box and the middle on a copy of the picture."""
    drawn: NDArray[np.uint8] = bgr.copy()
    cv2.rectangle(drawn, (found.left, found.top),
                  (found.left + found.width, found.top + found.height), (0, 255, 0), 1)
    cv2.drawMarker(drawn, (round(found.u), round(found.v)), (0, 255, 0),
                   cv2.MARKER_CROSS, markerSize=10, thickness=1)
    return drawn


def main() -> None:
    """Find the red box in the recorded picture, and say where it is."""
    heading('1. The picture')
    bgr: NDArray[np.uint8] = load_picture(PICTURE)
    height: int
    width: int
    height, width = bgr.shape[:2]
    print(f'{PICTURE.name}: {width} x {height} pixels, {bgr.dtype}, three colours per pixel')

    heading('2. The mask: the pixels of the colour we want')
    rough: NDArray[np.uint8] = colour_mask(bgr)
    mask: NDArray[np.uint8] = tidy(rough)
    print(f'pixels matching red: {int((rough > 0).sum()):,} before tidying, '
          f'{int((mask > 0).sum()):,} after')

    heading('3. The object')
    found: Found | None = largest_object(mask)
    if found is None:
        print('nothing of that colour in this picture')
        return
    print(f'middle at pixel u = {found.u:.1f}, v = {found.v:.1f}')
    print(f'bounding box: {found.width} x {found.height} pixels, '
          f'top-left corner at ({found.left}, {found.top})')
    print(f'the blob covers {found.pixels:,} pixels')

    OUT.mkdir(exist_ok=True)
    cv2.imwrite(str(OUT / 'found_by_colour.png'), annotate(bgr, found))
    cv2.imwrite(str(OUT / 'colour_mask.png'), mask)
    print(f'\nwrote {OUT / "found_by_colour.png"} and {OUT / "colour_mask.png"}')
    print('A pixel is only a direction, not a place. depth_of_object.py turns this')
    print('pixel into a position in metres, using the depth picture.')


if __name__ == '__main__':
    main()
