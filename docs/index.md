# REST Server for OptiPass

OptiPass™ is an application developed by Jesse O'Hanley at Ecotelligence®, LLC (https://www.ecotelligence.net/home/optipass).  

The application is written in Visual C++ and runs only in a Microsoft Windows environment.  To make it more accessible to web applications we developed this REST server.  While the server needs to run on a Windows system, clients (such as the one at https://github.com/conery/op-client) can run on any system, or even in a Docker container.

## Overview

The server has two main roles:

1. It manages tide gate data for one or more projects.  Each data set is a CSV file where records describe tide gates and other barriers.  Attributes include barrier names, locations, and so on.  The file also has the attributes OptiPass uses:  the cost to repair or replace a barrier, the upstream habitat impacted by the barrier, and the potential benefit of improving the barrier.
2. The server provides an API for running OptiPass.  A request to run OptiPass will include the IDs of barriers to include and the budget levels to use in order to generate ROI curves to show potential benefits from increasing budget levels.

It would be possible to assign these roles to different applications -- _e.g._ have separate servers for the data and OptiPass -- but we decided to combine them in order to minimize web traffic.  A client simply needs to know the names and locations of barriers, and descriptions of potential benefits.  The complete data set for the Oregon Coast, for example, is in a CSV file with over 1000 records and is 330KB.  Each request to run OptiPass uses a small fraction of this data, so it makes sense to keep the data on the server and send short descriptions to the client.

## Example

A common scenario for testing a FastAPI application is to launch Uvicorn (a Python-based web server) on the development system, passing it the name of the main function and specifying a port to listen to:

```bash
$ uvicorn app.main:app --port 8001
```

Then to request data from the server, simply send an HTML GET request to that port.  The response will be a JSON-encoded string that can easily be converted into a Python object.  This request asks the server for the names of all the datasets it manages:

```bash
$ curl localhost:8001/projects
["demo"]
```

The repository includes a test data set named `demo` (based on the examples in the OptiPass manual).  Others can be added simply by saving them in the `static` folder on the server (see [Data](data.md)).

## Implementation

The server is written entirely in Python, using FastAPI to manage requests.  The top level directories in the GitHub repository are:

- `app`: the main FastAPI application
- `bin`: a folder for `OptiPass.exe` and other executables
- `docs`:  notes for developers
- `static`:  CSV files for barrier data and restoration target descriptions
- `test`: unit tests

Detailed documentation for the Python code in the `app` folder can be found in [Modules](modules.md).  The test descriptions in [Unit Tests](tests.md) are a good place to find examples of how to call functions in the modules.

## Deployment

Developers who want to deploy the server using their own data need to do the following (described in more detail in [Installation](install.md)):

- set up a server that runs Microsoft Windows; this can be a stand-alone Windows system on a networked PC, or on a virtual machine at Amazon Web Services or another cloud service
- clone the repository (this can be done with a single PIP command)
- install the command line version of OptiPass in the `bin` directory (__OptiPass is not included with the repository__)
- add their data files to the `static` folder (see [Data](data.md))
- open a PowerShell window and type the command that starts the server

- (recommended) set up Nginx, Apache, or some other fully-featured web server and configure it as a reverse proxy



