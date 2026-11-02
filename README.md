# Observability

Tool to check observability of astronomical sources at various 
observatories and on different nights.

Requirements
------------
The code has been tested with Python 3.11 or newer.

Required packages:

    numpy, matplotlib, astroplan, astropy, pyqt5

Installation
------------
A virtual environment is strongly suggested. You can create it with all proper dependecies with:

    conda env create -f environment.yml
    conda activate observability

Otherwise, you can create it with your preferred name (or edit the .yml file) with:

    conda create --name your_env_name
    conda activate your_env_name

Then install Python dependencies:

    conda install PyQt5 numpy matplotlib astropy astroplan 

Usage
-----
To load the GUI, simply type

    python main.py

Users can show the observability of a single target by inserting the R.A. and Dec coordinates in the text boxes (in 
hh:mm:ss.s, dd:mm:ss.s format) or load a file with the following format:

Target_name R.A. Dec (coordinates can here be provided also in degrees)

Available observatories:

--> Paranal (Chile), La Silla (Chile), Cerro Tololo (Chile), La Palma (Canary islands, Spain), Mt. Graham (AZ, US), 
Mauna Kea (HI, US), Cerro Pachon (Chile)
