if ! command -v brew &> /dev/null
then
    echo "Installing Homebrew"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew is already installed"
fi

if ! command -v python3 &> /dev/null
then
    echo "Installing Python 3 using Homebrew"
    brew install python@3.9
else
    echo "Python 3 is already installed"
fi

if ! command -v conda &> /dev/null
then
    echo "Installing conda"
    brew install --cask anaconda
else
    echo "conda is already installed"
fi


wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O miniforge.sh


if ! conda list | grep -q cadquery
then
    echo "Installing CadQuery 2 using conda"
    conda install -c cadquery -c conda-forge cadquery=master
    export PATH="/usr/local/anaconda3/bin:$PATH"
else
    echo "CadQuery 2 is already installed"
fi

# pip install applescript
