# A REST Server for OptiPass™

The Migratory Fish Passage Optimization Tool (OptiPass), is an application developed by Jesse O'Hanley at [Ecotelligence® LLC](https://www.ecotelligence.net/home/optipass).  

The application is written in Visual C++ and runs only in a Microsoft Windows environment.  To make it more accessible to web applications we developed this REST server.  While the server needs to run on a Windows system, clients like [`op-client`](https://github.com/conery/op-client) can run on any system, or even in a Docker container.

## Overview

The server has two main roles:

1. It manages tide gate data for one or more projects.  Each data set is a collection of CSV files where records describe tide gates and other barriers. The files also have the information OptiPass needs:  the cost to repair or replace a barrier, the upstream habitat impacted by a barrier, and the potential benefit of improving a barrier.
2. The server provides an API for running OptiPass.  A request to run OptiPass will include the IDs of barriers to include and the budget levels to use in order to generate ROI curves to show potential benefits from increasing budget levels.

It would be possible to assign these roles to different applications -- _e.g._ have separate servers for the data and OptiPass -- but we decided to combine them in order to minimize web traffic.  A client simply needs to know the names and locations of barriers and short descriptions of potential benefits.  The complete data set for the Oregon Coast, for example, describes more than 1000 barriers and is about 350KB in size.
A client that uses this data just needs to send the server about 100 bytes of barrier names and optimization goals.

#### Example

To interact with an OptiPass server simply send it an HTML GET request.

Suppose there is a hypothetical server running at `tidegates-r-us.org`.
A request is a URL that contains the server name and a command that specifies what we want the server to do:

```
http://tidegates-r-us.org/X
```

where X is the command name.  For example, the `projects` command asks the server to send a list of all the data sets it manages.

To see what projects are managed by our hypothetical server we would start a terminal session and type a shell command that uses `curl`, a very simple web browser that sends a request to a server and prints the response:

```bash
$ curl http://tidegates-r-us.org/projects
['demo','oregon']
```

This output tells us our hypothetical server has data sets for the demo project (based on sample data in the OptiPass manual) and the Oregon Coast data set.

To run OptiPass, the command name is `optipass`.
The URL is a bit more complicated since we have to include options that specify region names, budget levels:

```bash
$ curl http://tidegates-r-us.org/optipass/oregon?regions=Coos&regions=Umpqua&...
{"summary":",budget,habitat,gates..."}
```

The server will build an input file for OptiPass using barriers from the regions named in the request.
It will use other arguments in the request to figure out the budget levels and other information and then run OptiPass once for each budget.
After the last run the data in the output files is collected into tables which are then sent back to the client.
The output above shows the first few column names in the summary table.

## Implementation

The server is written entirely in Python, using FastAPI to manage requests.  The top level directories in the GitHub repository are:

- `app`: the main FastAPI application
- `bin`: a folder for `OptiPass.exe` and other executables
- `docs`:  documentation (which you are reading now)
- `static`:  CSV files for barrier data and restoration target descriptions
- `test`: unit tests

Detailed documentation for the Python code in the `app` folder can be found in the [Modules](modules.md) section.  The test descriptions in [Unit Tests](tests.md) are a good place to find examples of how to call functions in the modules.

## Deployment

Developers who want to deploy the server using their own data need to do the following (described in more detail in [Installation and Configuration](install.md)):

- set up a server that runs Microsoft Windows; this can be a stand-alone Windows system on a networked PC, or a virtual machine at Amazon Web Services or another cloud service
- clone the repository (this can be done with a single PIP command)
- install the command line version of OptiPass in the `bin` directory (OptiPass is not included with the repository).
- add their data files to the `static` folder
- open a PowerShell window and type the command that starts the server

- (recommended) set up Nginx, Apache, or some other fully-featured web server and configure it as a reverse proxy



