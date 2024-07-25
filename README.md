# op-server
The Tidegate Optimization Tool is a decision support system developed by The Nature Conservancy to help landowners, conservationists, and other stakeholders allocate resources to restore tide gate infrastructure on the Oregon Coast (https://oregontidegates.org).

A key component of the system is a program named OptiPass, developed by Jesse O'Hanley (https://www.ecotelligence.net/home/optipass).  OptiPass is written in Visual C++ and runs only in a Microsoft Windows environment.

In order to avoid requiring end users to install OptiPass and the libraries it depends on we developed a web application so users simply have to connect to a server from their web browser.  

The web application has two components:  

- `op-server` is a REST server, written in Python using FastAPI, that provides the interface OptiPass.
- `op-client` (https://github.com/conery/op-client), also written in Python, uses Panel to display the GUI that end users connect to.

Since OptiPass is a Windows-only executable the server must be deployed on a Windows system, _e.g._ a VM running at Amazon Web Services.  The client can be run on any system, and a containerized version is also available at DockerHub.

