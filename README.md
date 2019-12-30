<p align="center">
  <img src="https://github.com/qkitgroup/tip/blob/master/logo/TIP_logo.png" alt="TIP" width="300">
</p>


tip
===
TIP is a program to monitor and regulate complex machines. 

TIP was developed having low temperature cryostates in mind, but is not limited to this.

Features:
===
  * periodic measurement of a arbitrary number of devices, e.g. thermometers
  * scalable client-server architecture with easy network access
  * PID control of the temperature
  * several drivers for resistance bridges
  * easy use of calibration tables
  * entirely written in python, only few external dependencies.
  * GUI for display and control of the temperatures

Installation:
===
  * requrements: a recent python3 installation with scipy and zmq. Some drivers need extra modules.
  * clone TIP to an appropriate directory
  * copy *settings.cfg* to *settings_local.cfg* and make changes there
  * start the tip server by changing into the tip directory and *python3 tip.py*


Authors:
===
 *  A. Schneider  (v1)/ KIT
 *  H. Rotzinger (v1-)/ KIT
