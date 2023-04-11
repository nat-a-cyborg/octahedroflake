# Octahedroflake: A 3D Fractal Inspired by the Sierpinski Triangle

This repository contains the CadQuery code and an accompanying Bash script to generate a 3D octahedron fractal called the "Octahedroflake." The Octahedroflake is a higher-dimensional analog of the Sierpinski Triangle, drawing inspiration from the Sierpinski Pyramid.


![Social Preview]https://repository-images.githubusercontent.com/626647438/cb055930-87fd-490b-80b1-48fa105da8bc

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

## File Descriptions

### octahedroflake.py

This Python script generates the Octahedroflake using CadQuery. It defines the parameters and functions necessary to create the fractal and exports the result as an STL file.

### run.sh

This Bash script streamlines running the \`octahedroflake.py\` script by offering a user-friendly interface. Specify various parameters, such as the number of iterations, layer height, nozzle diameter, and model height, through command-line arguments or interactive prompts. The script also provides a summary of the resulting model's dimensions and other characteristics.

## Restrictions on Selling the Model

The Octahedroflake model is for personal use only. Please refrain from selling this model or claiming it as your own work.

## Feedback and Contributions

As my first CadQuery project, I welcome any input or feedback. Please feel free to open an issue or submit a pull request if you have suggestions for improvements.

## License

This project falls under the GNU General Public License v3.0. You may use, modify, and distribute the code, but any modifications or derived works must also be released under the same license. For more details, consult the \`LICENSE\` file.
