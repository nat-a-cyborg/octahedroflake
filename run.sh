#!/bin/bash

set -euo pipefail

readonly REQUIRED_PYTHON_MINOR="3.11"
readonly DEFAULT_ITERATIONS=4
readonly DEFAULT_LAYER_HEIGHT=0.2
readonly DEFAULT_NOZZLE_DIAMETER=0.4
readonly DEFAULT_MODEL_HEIGHT=200.0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
VENV_DIR="$SCRIPT_DIR/venv"
readonly REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

PYTHON_BIN=""
no_prompt=false
iterations="$DEFAULT_ITERATIONS"
layer_height="$DEFAULT_LAYER_HEIGHT"
nozzle_diameter="$DEFAULT_NOZZLE_DIAMETER"
model_height="$DEFAULT_MODEL_HEIGHT"

if [[ -t 1 ]] && command -v tput >/dev/null 2>&1 && [[ -n "${TERM:-}" ]]; then
  readonly RED="$(tput setaf 1)"
  readonly GREEN="$(tput setaf 2)"
  readonly YELLOW="$(tput setaf 3)"
  readonly RESET="$(tput sgr0)"
else
  readonly RED=""
  readonly GREEN=""
  readonly YELLOW=""
  readonly RESET=""
fi

usage() {
  echo "Usage: $(basename "$0") [-h] [-i iterations] [-l layer_height] [-n nozzle_diameter] [-m model_height] [--no-prompt]"
}

help_message() {
  usage
  echo "Options:"
  echo "  -h, --help               show this help message and exit"
  echo "  -i, --iterations         number of fractal iterations (default: $DEFAULT_ITERATIONS)"
  echo "  -l, --layer-height       layer height in mm (default: $DEFAULT_LAYER_HEIGHT)"
  echo "  -n, --nozzle-diameter    nozzle diameter in mm (default: $DEFAULT_NOZZLE_DIAMETER)"
  echo "  -m, --model-height       desired model height in mm (default: $DEFAULT_MODEL_HEIGHT)"
  echo "      --no-prompt          run without interactive prompts"
  exit 0
}

require_value() {
  local option="$1"
  local value="${2-}"

  if [[ -z "$value" || "$value" == -* ]]; then
    echo "Error: $option requires a value." >&2
    exit 1
  fi
}

parse_args() {
  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      -h|--help)
        help_message
        ;;
      -i|--iterations)
        require_value "$1" "${2-}"
        iterations="$2"
        shift
        ;;
      -l|--layer-height)
        require_value "$1" "${2-}"
        layer_height="$2"
        shift
        ;;
      -n|--nozzle-diameter)
        require_value "$1" "${2-}"
        nozzle_diameter="$2"
        shift
        ;;
      -m|--model-height)
        require_value "$1" "${2-}"
        model_height="$2"
        shift
        ;;
      --no-prompt)
        no_prompt=true
        ;;
      *)
        echo "Invalid option: $1" >&2
        usage
        exit 1
        ;;
    esac
    shift
  done
}

select_python() {
  local candidate
  local version

  for candidate in python3 python3.11; do
    if ! command -v "$candidate" >/dev/null 2>&1; then
      continue
    fi

    version="$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)"
    if [[ "$version" == "$REQUIRED_PYTHON_MINOR" ]]; then
      PYTHON_BIN="$candidate"
      return
    fi
  done

  echo "Error: Python $REQUIRED_PYTHON_MINOR is required and was not found on PATH." >&2
  exit 1
}

ensure_venv() {
  cd "$SCRIPT_DIR"

  if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  else
    echo "Using existing virtual environment..."
  fi

  echo "Activating virtual environment..."
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
}

ensure_runtime_dependencies() {
  if ! python -c "import cadquery" >/dev/null 2>&1; then
    echo "Runtime dependencies not found. Installing from $(basename "$REQUIREMENTS_FILE")..."
    python -m pip install -r "$REQUIREMENTS_FILE"
  fi
}

get_parameters() {
  local user_iterations=""
  local user_layer_height=""
  local user_nozzle_diameter=""
  local user_model_height=""

  read -rp "Enter the number of iterations (default: $iterations): " user_iterations
  read -rp "Enter the layer height in mm (default: $layer_height): " user_layer_height
  read -rp "Enter the nozzle diameter in mm (default: $nozzle_diameter): " user_nozzle_diameter
  read -rp "Enter the model height in mm (default: $model_height): " user_model_height

  [[ -n "$user_iterations" ]] && iterations="$user_iterations"
  [[ -n "$user_layer_height" ]] && layer_height="$user_layer_height"
  [[ -n "$user_nozzle_diameter" ]] && nozzle_diameter="$user_nozzle_diameter"
  [[ -n "$user_model_height" ]] && model_height="$user_model_height"
}

main() {
  parse_args "$@"
  select_python
  ensure_venv

  echo "Upgrading pip..."
  python -m pip install --upgrade pip

  ensure_runtime_dependencies

  if [[ "$no_prompt" == false ]]; then
    get_parameters
  fi

  echo
  echo "${RED}***********${RESET}"
  echo "${RED}Parameters${RESET}"
  echo "${RED}***********${RESET}"
  echo "${YELLOW}Python path:${RESET}        $(command -v python)"
  echo "${YELLOW}Iterations:${RESET}         ${iterations}"
  echo "${YELLOW}Layer height:${RESET}       ${layer_height} mm"
  echo "${YELLOW}Nozzle diameter:${RESET}    ${nozzle_diameter} mm"
  echo "${YELLOW}Model height:${RESET}       ${model_height} mm"

  echo
  echo "${GREEN}Running the Python script...${RESET}"
  python "$SCRIPT_DIR/octahedroflake.py" \
    --iterations "$iterations" \
    --layer-height "$layer_height" \
    --nozzle-diameter "$nozzle_diameter" \
    --desired_height "$model_height"

  echo "${GREEN}Done.${RESET}"
  echo "Files are in ${SCRIPT_DIR}/output"

  if command -v open >/dev/null 2>&1; then
    open "${SCRIPT_DIR}/output"
  fi
}

main "$@"
