# op-server

## Overview

The Tidegate Optimization Tool is a decision support system developed by The Nature Conservancy to help landowners, conservationists, and other stakeholders allocate resources to restore tide gate infrastructure on the Oregon Coast (https://oregontidegates.org).

A key component of the system is a program named OptiPass, developed by Jesse O'Hanley (https://www.ecotelligence.net/home/optipass).  OptiPass is written in Visual C++ and runs only in a Microsoft Windows environment.

In order to avoid requiring end users to install OptiPass and the libraries it depends on we developed a web application so users simply have to connect to a server from their web browser.  

The web application has two components:  

- `op-server`, in this repo, is a REST server, written in Python using FastAPI, that provides the interface to OptiPass.
- `op-client` [https://github.com/conery/op-client](https://github.com/conery/op-client), also written in Python, uses Panel to display the GUI that end users connect to.

Since OptiPass is a Windows-only executable the server must be deployed on a Windows system, _e.g._ a VM running at Amazon Web Services.  The client can be run on any system, and a containerized version is also available at DockerHub.

## Model and View

To minimize web traffic, data files are kept on the server.
The server has been designed so other groups can add data for their own river systems.
The GitHub repo for the server includes a data set based on examples from the OptiPass Manual; the demo can be used as a template when configuring a new data set.

The client is written to be "data agnostic".
It gets all the information it needs -- the names and locations of tide gates, descriptions of restoration goals, and other data -- from the server.
Groups will not have to make any changes to the client in order to work with their own data.
Once the data is installed on a server, the client should be ready to display an interface to that data.

## Documentation

The full documentation for the client and server is online:

- [OP-Client](https://conery.github.io/op-client/) describes the GUI and how it communicates with the server.
- [OP-Server](https://conery.github.io/op-server/) has an overview of the data model, the REST API, instructions for installing and configuring a server, and developer documentation for the Python code and unit tests.
