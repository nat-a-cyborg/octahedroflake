#!/bin/bash

# -----------------------------------------------------------------------------
# 1. Enforce Python 3.11
#    - If default python != 3.11, attempt to switch to python3.11
#    - If python3.11 is not found, exit
# -----------------------------------------------------------------------------
REQUIRED_PYTHON_MINOR="3.11"

PYTHON="python3"
CURRENT_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)

if [[ "$CURRENT_VERSION" != "$REQUIRED_PYTHON_MINOR" ]]; then
  echo "Default python is version $CURRENT_VERSION; we need $REQUIRED_PYTHON_MINOR."
  if command -v python3.11 &>/dev/null; then
    PYTHON="python3.11"
    echo "Using $(command -v python3.11) instead."
  else
    echo "Error: python3.11 is not installed or not on PATH. Please install Python 3.11."
    exit 1
  fi
fi

# -----------------------------------------------------------------------------
# 2. Recreate and activate the virtual environment
# -----------------------------------------------------------------------------
SCRIPT="$(realpath "$0")"
DIR="$(dirname "$SCRIPT")"
cd "$DIR"

if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  "$PYTHON" -m venv venv || {
    echo "Failed to create virtual environment with $PYTHON. Exiting."
    exit 1
  }
else
  echo "Using existing virtual environment..."
fi

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source venv/bin/activate

# -----------------------------------------------------------------------------
# 3. Install or upgrade needed dependencies
# -----------------------------------------------------------------------------
if ! pip list --outdated | grep -q "^pip "; then
  echo "Upgrading pip..."
  pip install --upgrade pip
fi

if ! python -c "import cadquery" &> /dev/null; then
  echo "CadQuery not found. Installing..."
  pip install cadquery || {
    echo "Failed to install CadQuery. Exiting."
    exit 1
  }
fi

if ! python -c "import OCP" &> /dev/null; then
  echo "OCP not found. Installing..."
  pip install OCP || {
    echo "Failed to install OCP. Exiting."
    exit 1
  }
fi

# -----------------------------------------------------------------------------
# 4. Default parameters, usage, and argument parsing
# -----------------------------------------------------------------------------
readonly RED=$(tput setaf 1)
readonly GREEN=$(tput setaf 2)
readonly YELLOW=$(tput setaf 3)
readonly RESET=$(tput sgr0)

readonly DEFAULT_ITERATIONS=6
readonly DEFAULT_LAYER_HEIGHT=0.15
readonly DEFAULT_NOZZLE_DIAMETER=0.25
readonly DEFAULT_MODEL_HEIGHT=200.0

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

no_prompt=false

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    -h|--help)
      help_message
      ;;
    -i|--iterations)
      iterations="$2"
      shift
      ;;
    -l|--layer-height)
      layer_height="$2"
      shift
      ;;
    -n|--nozzle-diameter)
      nozzle_diameter="$2"
      shift
      ;;
    -m|--model-height)
      model_height="$2"
      shift
      ;;
    --no-prompt)
      no_prompt=true
      ;;
    *)
      echo "Invalid option: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

iterations=${iterations:-$DEFAULT_ITERATIONS}
layer_height=${layer_height:-$DEFAULT_LAYER_HEIGHT}
nozzle_diameter=${nozzle_diameter:-$DEFAULT_NOZZLE_DIAMETER}
model_height=${model_height:-$DEFAULT_MODEL_HEIGHT}

# If not no_prompt, prompt the user for overrides
get_parameters() {
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
  if ! $no_prompt; then
    get_parameters
  fi

  echo
  echo "${RED}***********${RESET}"
  echo "${RED}Parameters${RESET}"
  echo "${RED}***********${RESET}"
  echo "${YELLOW}Python path:${RESET}       $(command -v python)"
  echo "${YELLOW}Iterations:${RESET}        ${iterations}"
  echo "${YELLOW}Layer height:${RESET}      ${layer_height} mm"
  echo "${YELLOW}Nozzle diameter:${RESET}    ${nozzle_diameter} mm"
  echo "${YELLOW}Model height:${RESET}       ${model_height} mm"

  echo
  echo "${GREEN}Running the Python script...${RESET}"
  python "$DIR/octahedroflake.py" \
    --iterations "$iterations" \
    --layer-height "$layer_height" \
    --nozzle-diameter "$nozzle_diameter" \
    --desired_height "$model_height"

  echo "${GREEN}Done.${RESET}"
}

main

echo "Files are in ${DIR}/output"
if command -v open &> /dev/null; then
  open "${DIR}/output"
fi