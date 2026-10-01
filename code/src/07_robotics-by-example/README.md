# Robotics by Example — the code

This folder holds the programs behind Book 7, *Robotics by Example*. The book
works through one problem: several glasses of one kind stand on a table, and the
arm has to work out which pixels belong to which glass. The documents are in
`docs/07_robotics-by-example/`, and each solution document says which folder
here was built from it.

The code came from the `v5-pick-glasses` project, where the same problem is one
of several. It is kept as it was written, so that the two stay comparable.

## What is in each folder

Read the table as a list of folders, with what each one does and which document
explains it.

| Folder | What it is |
| --- | --- |
| `work_cell/` | The simulated cell itself: the table, the rack, the glasses and the camera. Every other folder imports it. |
| `problem-2-sim/` | Drawing a picture of the cell, and scoring an answer against the truth. The other three folders use both. |
| `problem-2-programmed/` | The written solution: find the glasses by clustering points on the table, then measure each one. |
| `problem-2-learned/` | The trained solution: a network that finds the glasses, and a ranker that chooses where to look next. |
| `problem-2-pretrained/` | The solutions that start from a large model trained elsewhere, then keep only the glasses. |
| `problem-2-results/` | What the runs produced, written down. |

## Running it

Each solution folder is its own pixi project, because they need different
libraries: the written one needs OpenCV and MuJoCo, and the trained ones need
PyTorch as well. Run them from inside their own folder, where their `Makefile`
and `pixi.toml` are, rather than from `code/`:

```bash
cd code/src/07_robotics-by-example/problem-2-programmed
make run
```

Each `pixi.toml` puts `work_cell/` and `problem-2-sim/` on the import path, so
those two are found as siblings without being installed.

## Two things to know

`COLCON_IGNORE` sits beside this file. The rest of `code/src/` is a ROS
workspace that `make build` compiles with colcon, and colcon builds every
package it finds underneath. The cell package here is not part of that
workspace, and it needs libraries the workspace environment does not have, so
the empty `COLCON_IGNORE` file tells colcon to walk past this whole folder.

The cell package came across whole, so it also contains the parts that belong to
other problems of the original project, such as the task runner and the report
writer. Nothing here uses them. They are left exactly as they were rather than
half-edited, and the paths they mention point at documents that live in that
project rather than this one.
