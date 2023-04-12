# APD-DT
A tool for automated creation and simulation of digital twins for smart pill dispenser devices. 
This work is a part of Welfare Technology Solution (WTS) project. 

[//]: # (The repository contains open-source implementation)


## Basic Requirements

* IDE: PyCharm
* Python: 3.9 or higher 

## Dependencies

* PyEcore: 0.13.1 
* Flask: 2.2.3
* Flask-RESTful: 0.3.9

## Usage Guide

### Step: 1 
Clone the repository using the following command.
```
git clone https://github.com/Simula-COMPLEX/WTSPublic.git
```
### Step: 2
Install dependencies following instructions:

* [PyEcore](https://pyecore.readthedocs.io/en/latest/user/install.html)
* [Flask](https://flask.palletsprojects.com/en/2.2.x/installation/)
* [Flask-RESTful](https://flask-restful.readthedocs.io/en/latest/installation.html)

### Step: 3
**Inputs settings**

Input settings can be change in different input files in `inputs` directory. 

**Running one DT**

To execute one DT, run `dt-main.py` file.  

**Running multiple DTs**

To execute multiple DT, run `dts-main.py` file. The number of DTs to run can be configured in `inputs/serial-numbers.txt` file.  