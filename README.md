# Interactive Imaging with CASA6

Experiments using dash/plotly with casa6 to implement interactive mask drawing 

To run, install dash in a python3 environment, start as "python Example_Interactive_Imager_App.py", and point a browser to http://127.0.0.1:8050

(1) Example_no_Casa6 : An example of a dash application that allows interactive mask drawing and iteration control. This uses a fake image reconstruction class that operates with noise and a few bright spots.

(2) Casa6_PySynthesisImager :  An example using the casa6 PySynthesisImager class.  Mask drawing is enabled but summary plots are more coarse-grained than above and iteration control is limited.

(3) Casa6_synthesis_tools : An example using the synthesisXXXX tools. The current version is identical to (2) in functionality, but will be edited to include iteration control options such as editing niter. cycleniter, etc.
