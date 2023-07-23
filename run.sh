#!/bin/bash

# Get the absolute path of the current script
SCRIPT="$(realpath "$0")"

# Get the directory name of the script
DIR="$(dirname "$SCRIPT")"

# Change the current working directory to the script directory
cd "$DIR"

# Define constants
readonly RED=$(tput setaf 1)
readonly GREEN=$(tput setaf 2)
readonly YELLOW=$(tput setaf 3)
readonly RESET=$(tput sgr0)

# Define default values
readonly DEFAULT_ITERATIONS=4
readonly DEFAULT_LAYER_HEIGHT=0.2
readonly DEFAULT_NOZZLE_DIAMETER=0.4
readonly DEFAULT_MODEL_HEIGHT=200.0

# Define usage and help message
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

# Set default values if no values provided
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

confirm() {
  if $no_prompt; then
    return 0
  else
    while true; do
      local gap_size=0.01
      local height_factor=0.7071
      local rib_width=$(echo "$nozzle_diameter * 2" | bc -l)

      size_multiplier=$(echo "scale=6; ($model_height - 0.5) / ((2^$iterations * ($nozzle_diameter * 4) * $height_factor * 2))" | bc)

      local edge_size=$(echo "$nozzle_diameter * 4 * $size_multiplier" | bc -l)
      local full_size=$(echo "2 ^ $iterations * $edge_size" | bc -l)

      echo "${YELLOW}Gap size:${RESET} ${gap_size} mm"
      echo "${YELLOW}Edge size:${RESET} ${edge_size} mm"
      echo "${YELLOW}Rib width:${RESET} ${rib_width} mm"
      echo "${YELLOW}Height factor:${RESET} ${height_factor}"
      echo "${YELLOW}Full size:${RESET} ${full_size} mm"
      echo "${YELLOW}Size multiplier:${RESET} ${size_multiplier}"
      echo "python3 $(dirname "$0")/octahedroflake.py" --iterations "$iterations" --layer-height "$layer_height" --nozzle-diameter "$nozzle_diameter" --size-multiplier "$size_multiplier"

      read -rp "${YELLOW}Do you want to continue? [Y/n]${RESET} " response
      case "$response" in
        [yY]|"")
          return 0
          ;;
        [nN])
          get_parameters
          ;;
        *)
          echo "Invalid response. Please enter 'y', 'n', or press the return key."
          ;;
      esac
    done
  fi
}


# Main function
main() {
  get_parameters
  confirm

  echo "${GREEN}Running the Python script...${RESET}"
  python3 "$(dirname "$0")/octahedroflake.py" --iterations "$iterations" --layer-height "$layer_height" --nozzle-diameter "$nozzle_diameter" --size-multiplier "$size_multiplier"
  echo "${GREEN}Done.${RESET}"
}

# Call the main function
main

if ! $no_prompt; then
  # Ask if the user wants to run the script again
  read -n 1 -r -p "${YELLOW}Press 'r' to run again, or any other key to exit...${RESET}" response
  if [[ "$response" =~ ^[rR]$ ]]; then
    echo -e "\nRunning script again..."
    exec "$0" "$@"
  else
    echo -e "\nExiting..."
  fi
fi

open "$DIR/output"
