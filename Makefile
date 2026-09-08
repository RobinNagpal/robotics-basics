# robotics-basics — one entry point for everything.
#
# The repo is split into areas. Each area is one ROS package under src/ and one
# folder under docs/. Area commands are named <area>.<action>, and each area
# keeps to two or three of them so this list stays readable as areas are added.
#
# Run `make` on its own to see what is available.

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Run a command inside the pixi env with the workspace overlay sourced.
ros = pixi run bash -c 'source install/setup.bash && $(1)'

.PHONY: help setup doctor build test lint clean shell \
        rviz.demo rviz.check arm.learn arm.demo arm.watch

help: ## Show this help
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} \
		/^##@/ { printf "\n  \033[1m%s\033[0m\n", substr($$0, 5) } \
		/^[a-zA-Z_.-]+:.*?##/ { printf "    \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "  Area commands are <area>.<action>. Docs for an area are in docs/<area>/."
	@echo ""

##@ Project

setup: ## Install the environment (first run downloads ROS 2, a few gigabytes)
	pixi install

build: ## Build every area
	pixi run build

test: ## Run every test
	pixi run test

lint: ## Check code style everywhere
	pixi run flake8 src/ docs/ --max-line-length=100

clean: ## Remove build/, install/ and log/
	pixi run clean

shell: build ## Shell with ROS ready, for typing ros2 commands
	$(call ros,exec bash)

# NOTE: not written with $(call ros,...) — that helper wraps the command in
# single quotes, so a printf format string would end the quoting early.
doctor: ## Print versions of everything that matters
	@printf "%-14s %s\n" "pixi" "$$(pixi --version 2>&1)"
	@pixi run bash -c 'source install/setup.bash 2>/dev/null; \
		printf "%-14s %s\n" "python"     "$$(python --version 2>&1)"; \
		printf "%-14s %s\n" "ROS distro" "$$ROS_DISTRO"; \
		printf "%-14s %s\n" "areas"      "$$(ls src | tr "\n" " ")"'

##@ rviz — a marker in a moving frame

rviz.demo: build ## Launch the node and RViz: a ball circling a grid
	$(call ros,ros2 launch rviz_basics marker_demo.launch.py)

rviz.check: ## Show what the demo is publishing (run rviz.demo first)
	@pixi run bash -c 'source install/setup.bash; \
		ros2 topic list | grep -qx /visualization_marker || \
			{ echo "Nothing is publishing. Start it with: make rviz.demo"; exit 1; }; \
		echo "--- topics ---"; ros2 topic list; \
		echo; echo "--- one marker ---"; ros2 topic echo --once /visualization_marker | head -8; \
		echo; echo "--- one transform ---"; ros2 topic echo --once /tf | head -16'

##@ arm — position, frames and transforms

arm.learn: build ## Work through the maths, steps 1 to 3, then exit
	@$(call ros,ros2 run arm_transforms arm_step1_positions)
	@echo; $(call ros,ros2 run arm_transforms arm_step2_frames)
	@echo; $(call ros,ros2 run arm_transforms arm_step3_chain)

arm.demo: build ## Step 4: publish the arm to TF and draw it in RViz
	$(call ros,ros2 launch arm_transforms arm_demo.launch.py)

arm.watch: build ## Step 5: ask TF where the gripper is (run arm.demo first)
	$(call ros,ros2 run arm_transforms arm_step5_lookup)
