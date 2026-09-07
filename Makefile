# robotics-basics — one entry point for running the project.
#
# Every target runs inside the pixi environment with the colcon overlay already
# sourced, so there is never a `pixi shell` or `source install/setup.bash` step
# to remember. Run `make` on its own to see what is available.

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Run a command inside the pixi env with the workspace overlay sourced.
ros = pixi run bash -c 'source install/setup.bash && $(1)'

.PHONY: help setup build test lint demo node rviz topics marker tf frames graph shell doctor clean

help: ## Show this help
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} \
		/^##@/ { printf "\n  \033[1m%s\033[0m\n", substr($$0, 5) } \
		/^[a-zA-Z_-]+:.*?##/ { printf "    \033[36m%-9s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "  Targets marked [live] need 'make demo' running in another terminal."
	@echo ""

##@ Setup

setup: ## Resolve and install the environment (first run downloads ROS 2, a few GB)
	pixi install

# NOTE: this recipe deliberately does not use $(call ros,...) — that helper wraps
# the command in single quotes, so any single quote in the command (a printf
# format string, say) silently terminates the quoting and mangles the output.
doctor: ## Print versions of everything that matters
	@printf "%-14s %s\n" "pixi" "$$(pixi --version 2>&1)"
	@pixi run bash -c 'source install/setup.bash 2>/dev/null; \
		printf "%-14s %s\n" "python"     "$$(python --version 2>&1)"; \
		printf "%-14s %s\n" "ROS distro" "$$ROS_DISTRO"; \
		printf "%-14s %s\n" "rviz2"      "$$(command -v rviz2)"; \
		printf "%-14s %s\n" "ROS pkgs"   "$$(ros2 pkg list | wc -l | tr -d " ") available"; \
		printf "%-14s %s\n" "workspace"  "$$(ls install 2>/dev/null | grep -c rviz_basics) built package(s)"'

##@ Build & test

build: ## Build the colcon workspace
	pixi run build

test: ## Run the unit tests
	pixi run test

lint: ## Check code style
	pixi run flake8 src/ --max-line-length=100

clean: ## Remove build/, install/ and log/
	pixi run clean

##@ Run it

demo: ## Launch the node + RViz2 together — this is the one to start with
	pixi run demo

node: ## Run only the marker publisher (no RViz)
	pixi run node

rviz: build ## Run only RViz2 with the saved config
	$(call ros,rviz2 -d src/rviz_basics/rviz/marker_demo.rviz)

##@ Inspect the running system

topics: ## [live] List active topics
	$(call ros,ros2 topic list)

marker: ## [live] Print one marker message
	$(call ros,ros2 topic echo --once /visualization_marker)

tf: ## [live] Stream the world -> marker_frame transform (Ctrl-C to stop)
	$(call ros,ros2 run tf2_ros tf2_echo world marker_frame)

frames: ## [live] Snapshot the TF tree to a PDF and open it
	@mkdir -p build/tf_frames
	$(call ros,cd build/tf_frames && ros2 run tf2_tools view_frames)
	@open build/tf_frames/frames_*.pdf

graph: ## [live] Open rqt_graph to see nodes and topics
	$(call ros,ros2 run rqt_graph rqt_graph)

##@ Escape hatch

shell: build ## Open a shell with ROS + the workspace sourced (plain ros2 commands work)
	$(call ros,exec bash)
