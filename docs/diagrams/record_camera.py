"""Record the Gazebo captures that the camera diagrams are drawn from.

Run with:  pixi run python docs/diagrams/record_camera.py

The pictures in the camera docs are real captures from the camera_one_box
simulation, not drawings. For each camera setting below, this starts the
simulation with that setting, saves one capture with save_snapshot, and stops
it again. The captures go to docs/diagrams/captures/camera/<name>/, and
docs/diagrams/camera.py draws the diagrams from them.

Rerun it after changing the world, the camera description or the settings.
It takes about a minute. Run `make build` first.
"""

import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[2]
CAPTURES = REPO_ROOT / 'docs' / 'diagrams' / 'captures' / 'camera'

#: name: (pixels across, pixels down, field of view in degrees). "wrist" is the
#: camera the doc uses. The others change one thing at a time, for section 7
#: of the basics doc, and "tiny" is small enough to see every pixel.
SETTINGS = {
    'wrist': (320, 240, 60),
    'wide': (320, 240, 90),
    'narrow': (320, 240, 30),
    'hires': (640, 480, 60),
    'lowres': (80, 60, 60),
    'tiny': (16, 12, 60),
}


def ros(command: str) -> list[str]:
    """Wrap a command so it runs with the workspace sourced."""
    return ['bash', '-c', f'source install/setup.bash && exec {command}']


def record(name: str, width: int, height: int, hfov_deg: int) -> None:
    """Start the simulation with one camera setting, save a capture, stop it."""
    out = CAPTURES / name
    shutil.rmtree(out, ignore_errors=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    simulation = subprocess.Popen(
        ros('ros2 launch camera_one_box one_box.launch.py rviz:=false '
            f'width:={width} height:={height} hfov_deg:={hfov_deg}'),
        cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True)
    try:
        time.sleep(6)       # Gazebo loads the world and the camera appears in it
        subprocess.run(ros(f'ros2 run camera_one_box save_snapshot {out}'),
                       cwd=REPO_ROOT, check=True, timeout=90)
    finally:
        simulation.send_signal(signal.SIGINT)
        try:
            simulation.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(simulation.pid, signal.SIGKILL)
    print(f'{name}: {width} x {height}, {hfov_deg}° -> {out.relative_to(REPO_ROOT)}')


if __name__ == '__main__':
    names = sys.argv[1:] or list(SETTINGS)
    for name in names:
        record(name, *SETTINGS[name])
