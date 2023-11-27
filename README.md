# Octahedroflake: A 3D Fractal Sculpture Inspired by the Sierpinski Triangle

This repository contains the CadQuery code and an accompanying Bash script to generate a 3D octahedron fractal called the "Octahedroflake." The Octahedroflake is a higher-dimensional analog of the Sierpinski Triangle.

[![Social Preview](https://repository-images.githubusercontent.com/626647438/cb055930-87fd-490b-80b1-48fa105da8bc)](https://www.printables.com/model/432767)

## Table of Contents

- [Pre-generated Models](#pre-generated-models)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [File Descriptions](#file-descriptions)
- [Restrictions on Selling the Model](#restrictions-on-selling-the-model)
- [Feedback and Contributions](#feedback-and-contributions)
- [License](#license)

## Pre-generated Models

Download pre-generated Octahedroflake models using the following link:

[Pre-generated Octahedroflake Models](https://www.printables.com/model/432767)

This link also provides slicing and printing instructions, as well as photos of printed models created by users.

## Prerequisites

To utilize this repository, ensure you have CadQuery 2.0 or a later version installed on your system. Follow the installation instructions from the official CadQuery documentation:

[CadQuery Installation Instructions](https://cadquery.readthedocs.io/en/latest/installation.html)

## Usage

Generate an Octahedroflake by running the \`run.sh\` script in your terminal:

```
./run.sh
```

You can also customize the parameters of the generated fractal using optional command-line arguments. For example:

```
./run.sh -i 4 -l 0.2 -n 0.4 -m 150
```

To view a full list of command-line options, run:

```
./run.sh -h
```

### Running directly

```
python3 /home/octahedroflake.py --iterations 6 --layer-height 0.2 --nozzle-diameter 0.4 --size-multiplier 1.377628
```

## File Descriptions

### [octahedroflake.py](https://github.com/nat-a-cyborg/octahedroflake/blob/main/octahedroflake.py)

This Python script generates the Octahedroflake using CadQuery. It defines the parameters and functions necessary to create the fractal and exports the result as an STL file.

### [run.sh](https://github.com/nat-a-cyborg/octahedroflake/blob/main/run.sh)

This Bash script streamlines running the \`octahedroflake.py\` script by offering a user-friendly interface. Specify various parameters, such as the number of iterations, layer height, nozzle diameter, and model height, through command-line arguments or interactive prompts. The script also provides a summary of the resulting model's dimensions and other characteristics.

## Restrictions on Selling the Model

The Octahedroflake model is for personal use only. Please refrain from selling this model or claiming it as your own work.

## Feedback and Contributions

As my first CadQuery project, I welcome any input or feedback. Please feel free to open an issue or submit a pull request if you have suggestions for improvements.

## Docker

### BUILD

`docker build -t cadquery:fractal .`

### RUN

`docker run -v $(pwd)/output:/home/output -it cadquery:fractal`

## License

Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
