# APD-DT
A tool for automated creation and operation of digital twins for automatic medicine dispensers. 
This work is a part of the Welfare Technology Solution (WTS) project. 

[//]: # (The repository contains open-source implementation)

## Related Publication
* Hassan Sartaj, Shaukat Ali, Tao Yue, and Kjetil Moberg. "Model‐based digital twins of medicine dispensers for healthcare IoT applications." *Software: Practice and Experience* (2024); 1-21. doi: 10.1002/spe.3311 [[Preprint]](https://arxiv.org/abs/2312.04662)

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

Input settings can be changed in different input files in `APD-DT/inputs` directory. 

**Running one DT**

To execute one DT, run `dt-main.py` file.  

**Running multiple DTs**

To execute multiple DTs, run `dts-main.py` file. The number of DTs to run can be configured in `APD-DT/inputs/serial-numbers.txt` file.

**Communicating with DT(s)**

Use the APIs provided in the mapping file, add the serial number of the specific dispenser(s), and use Postman or any other client to send HTTP requests to the DT(s) and get a response from the DT(s). 
The supported data interchange format is JSON. 
