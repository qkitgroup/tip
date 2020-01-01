<p align="center">
  <img src="https://github.com/qkitgroup/tip/blob/master/logo/TIP_logo.png" alt="TIP" width="300">
</p>


tip
===
TIP is a program to monitor and regulate complex machines and was developed having a low temperature cryostate in mind. It is, however, not limited to that.

Features:
===
  * periodic measurement of a arbitrary number of devices, e.g. thermometers
  * scalable client-server architecture with easy network access
  * PID control of the temperature
  * several drivers for resistance bridges
  * easy use of calibration tables
  * integrates well with QKIT
  * GUI for display and control of the temperatures
  * entirely written in python, only few external dependencies.

Installation:
===
  * requrements: A recent python3 installation with *scipy* and *zmq*, the gui is based on *pyqt5* and *pyqtgraph*.
  * some drivers need extra modules
  * clone TIP to an appropriate directory
  * copy *settings.cfg* to *settings_local.cfg* and make changes there
  * start the tip server by changing into the tip directory and execute *python3 tip.py*


Authors:
===
 *  A. Schneider  (v1)/ KIT
 *  H. Rotzinger (v1-)/ KIT
