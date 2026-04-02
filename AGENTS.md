# Repository Guidelines

## Project Structure & Module Organization
`octahedroflake.py` is the main generator and contains the CadQuery model, CLI parsing, caching, and export logic. `run.sh` is the primary local entry point; it bootstraps a `venv`, installs dependencies from `requirements.txt`, prompts for parameters, and writes generated files to `output/`. Supporting assets live at the repo root: `logo_stamp.step` is imported geometry, `octahedroflake.ipynb` is an exploratory notebook, `tests/` holds lightweight regression coverage, and `Dockerfile` provides a containerized runtime. Generated directories such as `output/` and `part_cache/` are local artifacts and should stay uncommitted.

## Build, Test, and Development Commands
Run `./run.sh` for the interactive workflow. Use `./run.sh --no-prompt -i 4 -l 0.2 -n 0.4 -m 200` for repeatable local checks. Run the generator directly with `python3.11 octahedroflake.py --iterations 4 --layer-height 0.2 --nozzle-diameter 0.4 --desired_height 200` when debugging the Python entry point. Install development dependencies with `python3.11 -m pip install -r requirements-dev.txt`. Lint with `python3.11 -m pylint octahedroflake.py tests/test_octahedroflake.py`. Run tests with `python3.11 -m unittest discover -s tests`. Build the container with `docker build -t octahedroflake .` if you need an isolated CadQuery environment.

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, snake_case for functions and variables, and UPPER_CASE for module constants. Formatting is configured through YAPF in `.style.yapf` with a 130-column limit; use `yapf -i octahedroflake.py` before finalizing a change that meaningfully restructures the file. Keep command-line flags and cache/output directory names consistent with the current script conventions. Shell changes should remain Bash-compatible and preserve the repo’s simple, linear setup flow.

## Testing & Validation
Before submitting changes, run `python3.11 -m unittest discover -s tests`, `python3.11 -m pylint octahedroflake.py tests/test_octahedroflake.py`, and execute `./run.sh --no-prompt` with representative parameters. When generation behavior changes, confirm STL/STEP output lands in `output/` without cache-related regressions. CI currently lints on Python 3.10, while `run.sh` enforces Python 3.11 locally, so avoid version-specific changes unless both paths are verified.

## Working Style
Work directly on the `develop` branch unless the maintainer explicitly asks for a separate branch. Use plain `git` commands for commits and pushes; do not introduce a PR-based workflow or `gh`-specific steps unless the maintainer asks for them. Keep commit titles imperative, focused, and under roughly 72 characters.
Use `Nat Johnson <nat@a-cyborg.com>` as the git author and committer identity for commits in this repository.

## Natural Language Generation Requests
Treat simple requests like “make a model 480 high at order 3” as a request to run the generator, not just explain the command. Translate that example to `./run.sh --no-prompt -i 3 -m 480` and use the repo defaults for any unspecified print settings:

- layer height: `0.2`
- nozzle diameter: `0.4`
- branding: off unless the user asks for it

When fulfilling these requests:

- run the command instead of only describing it
- report the output file path
- report the generator’s logged full height if it differs from the requested `--desired_height`
- ask for clarification only when a missing parameter materially changes the output and there is no sensible repo default
