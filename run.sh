#!/bin/bash

# Check Python version
PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
if [[ "$PY_VERSION" == "3.13" ]]; then
  echo "Error: Python 3.13 detected. The OCP package currently fails to install on Python 3.13 (Apple silicon)."
  echo "Please install and use Python 3.11 (for example, via Homebrew: 'brew install python@3.11') and recreate your virtual environment."
  exit 1
fi

# Get the absolute path of the current script and its directory
SCRIPT="$(realpath "$0")"
DIR="$(dirname "$SCRIPT")"
cd "$DIR"

# --- Setup Virtual Environment ---
if [ -z "$VIRTUAL_ENV" ]; then
  if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || { echo "Failed to create virtual environment. Exiting."; exit 1; }
  fi
  echo "Activating virtual environment..."
  source venv/bin/activate
fi

# Upgrade pip (optional but recommended)
pip install --upgrade pip

# --- Install Dependencies ---
if ! python3 -c "import cadquery" &> /dev/null; then
  echo "CadQuery not found. Installing CadQuery..."
  pip install cadquery || { echo "Failed to install CadQuery. Exiting."; exit 1; }
fi

if ! python3 -c "import OCP" &> /dev/null; then
  echo "OCP module not found. Installing OCP dependency..."
  pip install OCP || { echo "Failed to install OCP. Exiting."; exit 1; }
fi

# Define terminal colors
readonly RED=$(tput setaf 1)
readonly GREEN=$(tput setaf 2)
readonly YELLOW=$(tput setaf 3)
readonly RESET=$(tput sgr0)

# Define default values
readonly DEFAULT_ITERATIONS=4
readonly DEFAULT_LAYER_HEIGHT=0.2
readonly DEFAULT_NOZZLE_DIAMETER=0.4
readonly DEFAULT_MODEL_HEIGHT=200.0

usage() {
  echo "Usage: $(basename "$0") [-h] [-i iterations] [-l layer_height] [-n nozzle_diameter] [-m model_height] [--no-prompt]"
}

help_message() {
  usage
  echo "Options:"
  echo "  -h, --help               show this help message and exit"
  echo "  -i, --iterations         set the number of iterations (default: $DEFAULT_ITERATIONS)"
  echo "  -l, --layer-height       set the layer height in mm (default: $DEFAULT_LAYER_HEIGHT)"
  echo "  -n, --nozzle-diameter    set the nozzle diameter in mm (default: $DEFAULT_NOZZLE_DIAMETER)"
  echo "  -m, --model-height       set the model height in mm (default: $DEFAULT_MODEL_HEIGHT)"
  echo "      --no-prompt          run without user prompts, using provided values or defaults"
  exit 0
}

no_prompt=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
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

# Set default values if not provided
iterations=${iterations:-$DEFAULT_ITERATIONS}
layer_height=${layer_height:-$DEFAULT_LAYER_HEIGHT}
nozzle_diameter=${nozzle_diameter:-$DEFAULT_NOZZLE_DIAMETER}
model_height=${model_height:-$DEFAULT_MODEL_HEIGHT}

get_parameters() {
  if ! $no_prompt; then
    read -rp "Enter the number of iterations (default: $iterations): " user_iterations
    read -rp "Enter the layer height in mm (default: $layer_height): " user_layer_height
    read -rp "Enter the nozzle diameter in mm (default: $nozzle_diameter): " user_nozzle_diameter
    read -rp "Enter the model height in mm (default: $model_height): " user_model_height

    [[ -n "$user_iterations" ]] && iterations=$user_iterations
    [[ -n "$user_layer_height" ]] && layer_height=$user_layer_height
    [[ -n "$user_nozzle_diameter" ]] && nozzle_diameter=$user_nozzle_diameter
    [[ -n "$user_model_height" ]] && model_height=$user_model_height
  fi

  echo "${RED}***********${RESET}"
  echo "${RED}Parameters${RESET}"
  echo "${RED}***********${RESET}"
  echo "${YELLOW}Iterations:${RESET} ${iterations}"
  echo "${YELLOW}Layer height:${RESET} ${layer_height} mm"
  echo "${YELLOW}Nozzle diameter:${RESET} ${nozzle_diameter} mm"
  echo "${YELLOW}Model height:${RESET} ${model_height} mm"
}

# Compute the size multiplier (used by the Python script)
compute_size_multiplier() {
  local height_factor=0.7071
  size_multiplier=$(echo "scale=6; ($model_height - 0.5) / ((2^$iterations * ($nozzle_diameter * 4) * $height_factor * 2))" | bc -l)
}

confirm() {
  while true; do
    local gap_size=0.01
    local height_factor=0.7071
    local rib_width
    rib_width=$(echo "$nozzle_diameter * 2" | bc -l)

    compute_size_multiplier

    local edge_size
    edge_size=$(echo "$nozzle_diameter * 4 * $size_multiplier" | bc -l)
    local full_size
    full_size=$(echo "2^$iterations * $edge_size" | bc -l)

    echo "${YELLOW}Gap size:${RESET} ${gap_size} mm"
    echo "${YELLOW}Edge size:${RESET} ${edge_size} mm"
    echo "${YELLOW}Rib width:${RESET} ${rib_width} mm"
    echo "${YELLOW}Height factor:${RESET} ${height_factor}"
    echo "${YELLOW}Full size:${RESET} ${full_size} mm"
    echo "${YELLOW}Size multiplier:${RESET} ${size_multiplier}"
    echo "python3 $DIR/octahedroflake.py --iterations $iterations --layer-height $layer_height --nozzle-diameter $nozzle_diameter --size-multiplier $size_multiplier"

    read -rp "${YELLOW}Do you want to continue? [Y/n]${RESET} " response
    case "$response" in
      [yY]|"")
        break
        ;;
      [nN])
        get_parameters
        ;;
      *)
        echo "Invalid response. Please enter 'y' or 'n'."
        ;;
    esac
  done
}

main() {
  get_parameters
  if $no_prompt; then
    compute_size_multiplier
  else
    confirm
  fi

  echo "${GREEN}Running the Python script...${RESET}"
  python3 "$DIR/octahedroflake.py" --iterations "$iterations" --layer-height "$layer_height" --nozzle-diameter "$nozzle_diameter" --size-multiplier "$size_multiplier"
  echo "${GREEN}Done.${RESET}"
}

# Execute main routine
main

echo "Files are in $DIR/output"
if command -v open >/dev/null 2>&1; then
  open "$DIR/output"
fi