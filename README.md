# Grainsizer X #

A graphical interface that allows quick, easy and accurate grain size measurement of digital micrographs.

![Grainsizer Demo Gif](https://media.giphy.com/media/cLhovdZAttRcWz1nnz/giphy.gif)

## Method ##

Grain size is found using the linear intercept method.

    This involves drawing a number of lines across the micrograph and 
    counting the number of times these lines intercept a grain boundary.

Then the following equation is used.

average grain size (m) = magnification (m/px) * total line length (px) / number of intercepts  

The app enables you to

- Easily find the magnification

- Accurately highlight all grain boundaries

- Create horizontal and vertical intercept lines

The grainsize is then worked out automatically by counting the number of intercepts.

## Installation ##

The standalone .exe file can be downloaded from my personal onedrive [here](https://1drv.ms/u/s!AnQ8aqbFsILIge8pbSo0IAwAOHWXUw?e=6D9Gh0).

To launch the program manually simply download the Grainsizer App folder and run the App Script python file.

    Several additional libraries must be pip installed for the app to run. These are PySimpleGUI 
    if running on Anaconda plus Numpy, Pillow and scikit-image if running on base Python.

Creating the .exe script on your own machine requires a few more steps. This can be done a couple different ways but below is how i have done this.

- Install the VSCode editor with Python [from here](https://code.visualstudio.com/docs/python/python-tutorial)

- Create a new virtual enviroment following [this](https://stackoverflow.com/a/61092957/13688987) method (make sure to complete all steps)

- Pip install PySimpleGUI, Numpy, Pillow, scikit-image and auto-py-to-exe

- Type auto-py-to-exe into the powershell and press enter

- Enter in all the following settings into the popup
    
    - Browse for the App (PyInstaller Paths) python file in the script location

    - Click the One File button under Onefile

    - Click the Window Based button under Console Window

    - Browse for the Icon.ico file under Icon

    - Browse for Coloured Test, Grey Test, Icon and Final Logo images under additional files

    - Set the name to Grainsizer X just under General Options after you click Advanced

    - Browse for your desktop for the Output Directory after you click Settings

    - Click CONVERT .PY to .EXE

After about 30 seconds and the program should pop up on your desktop!

## Usage ##

Work through the left column from top to bottom to complete the process. Note the mouse controls on the startup logo. See the Grainsizer X Example gif for a quick demo.

### Tips

While this app should return accurate results given grain boundaries are highlighted accurately and intercept spacing is minimized, it is a good idea to average out the result from multiple micrographs of the same sample. This ensures the result is most accurate and representative of the entire sample.

Also its worth taking the extra time to get the threshold setting perfect.

![Grainsizer Threshold Example](https://media.giphy.com/media/1ouSGxPt7wI5FlmkE7/giphy.gif)

This can be difficult as setting it too high means you will have to draw on extra missed grain boundaries however setting it too low will mean imperfections will be registered as grain boundaries and the measured grain size will be lower than the true value.

## Support ##

If you encounter any bugs or are finding any part of the process difficult please do let me know by raising an issue on GitHub. I'll do the best i can to reply within 24 hours.

## Roadmap ##

Right now i am working on simplifying the app's process and meeting industry measurement standards. Some of these new features include:

- Automatic best guess thresholding

- A remove small spikes button to reduce the error caused by over thresholding

- Diagonal and circular red intercept lines to improve accuracy for non symetrical grains

- A stats panel for exact accuracy information 

If you have any ideas for new features or changes please also raise an issue on GitHub. Origionally this was just a fun summer project but I am really keen to do all i can to make the app as useful as possible for any given workload.

## Authors and acknowledgment ##

This program was written by me Ayham Saffar however i could not have done it on my own. Thank you João Quinta da Fonseca from the University of Manchester for first teaching this method and giving feedback early on. Also thanks Mike & Jason from the PySimpleGUI GitHub for creating your brilliant library and all your great support.
