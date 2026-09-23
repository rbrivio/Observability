# Observability

Tool to check observability of astronomica sources at various observatories and on different nights.


Requirements
------------

    numpy, matplotlib, pyqt5, astroplan, astropy

Usage
-----
Download the zip file and unpack it. Then simply type

    python main_obs.py

To load the GUI.

Users can show the observability of a single target by inserting the R.A. and Dec coordinates in the text boxes (in 
hh:mm:ss.s, dd:mm:ss.s format) or load a file with the following format:

Target_name R.A. Dec (coordinates can here be provided also in degrees)

Available observatories:

    Paranal (Chile), La Silla (Chile), Cerro Tololo (Chile), La Palma (Canary islands, Spain), LBT (Mt. Graham AZ, US), 
Gemini-North (Mauna Kea, HI, US), Gemini-South
 (Cerro Pachon, Chile)
