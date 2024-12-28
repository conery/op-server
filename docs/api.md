# API

Once a server is set up and running, we can retrieve data by sending it an HTTP request.

The general format of a request URL is
```
http://<server>/<command>/<args>
```

For example, if a server is running at `tidegates-r-us.org` and you want to retrieve target descriptions for the demo project, send it the "targets" command with the project name as an argument:

```
http://tidegates.org-r-us/targets/demo
```

The server will respond with a dictionary (in JSON format) that has the project name and a string that can be converted into a Pandas dataframe.

In the examples below we'll assume the server has been started on the local machine and is listening on port 8000 (the default).
To launch the server, `cd` to the project directory and type

```
$ uvicorn app.main:app
```

Then to test a command just type its URL in a `curl` command:

```
$ curl http://localhost:8000/targets/demo
{"project":"demo","targets":"abbrev,long,short,label,infra\nT1,Target 1,Targ1,Target 1 (km),False\nT2,Target 2,Targ2,Target 2 (km),False","layout":"T1 T2"}
```

## `projects`

The `projects` command returns a list of names of projects configured on the server.

Example:

```
$ curl http://localhost:8000/projects
["demo","oregon"]
```

## `barriers/P`

The `barriers` command takes one argument, the name of a project.
It returns a dictionary that has the project name and a string that can be loaded into a Pandas dataframe.

Example:

```
$ curl http://localhost:8000/barriers/demo
{"project":"demo","barriers":"ID,region,DSID,name,cost,X,Y,NPROJ,comment\nA,Trident,NA,,250000,330,202,1,\nB,Red Fork,A,,120000,235,230,1,\nC,Red Fork,B,,70000,148,220,1,\nD,Trident,A,,NA,195,335,0,\nE,Trident,D,,100000,100,440,1,\nF,Trident,D,,50000,125,450,1,"}%  
```

Here is example of how a client can convert the CSV string into a dataframe:

```python
    req = f'{server}/barriers/{project}'
    resp = requests.get(req)
    if resp.status_code != 200:
        raise OPServerError(resp)
    buf = StringIO(resp.json()['barriers'])
    df = pd.read_csv(buf)
```

#### A Note About Passability Values

The table returned by the `barriers` command is from the `barriers.csv` file in the `static` folder for the project.  The passability data in `passability.csv` is not returned, assuming most clients just need the names and basic information about barriers and targets.

## `targets/P`

The `targets` command takes one argument, the name of a project.
It returns a dictionary with three entries:

* the target name
* a CSV string that can be converted into the target table (_i.e._ the contents of the `targets.csv` file for the project)
* a text string with the suggested layout for displaying target names in a GUI

Example:

```
$ curl http://localhost:8000/targets/demo
{"project":"demo","targets":"abbrev,long,short,label,infra\nT1,Target 1,Targ1,Target 1 (km),False\nT2,Target 2,Targ2,Target 2 (km),False","layout":"T1 T2"}% 
```

## `colnames/P`

If a project has more than one way of connecting target names to benefit values a server allows a user to put more than one mapping file in the `static` folder.

An example of where this feature is used is in the Oregon coast data.
That data set has two differents sets of habitat values for infrastructure targets, some defined for current climate values and a second set that assume temperatures rise and more land is inundated at high tide.  That project has two column name mapping files, one named `current.csv` and one named `future.csv`.

The `colnames` command returns a dictionary that tells a client whether or not a project has alternative column name mappings.
The dictionary has two entries:  a `name` field and a `files` field with a list of file names.

The dictionary returned for the Oregon coast project looks like this:
```
{ 'name': 'climate', 'files': ['current.csv', 'future'csv] }
```
This allows the GUI managed by the client to create a menu or a switch labled "climate" with two alternatives, one for "current" and one for "future".

The demo project has only one mapping, so the dictionary has None for the name and a single file name in the list:
```
$ curl http://localhost:8000/colnames/demo
{"name":null,"files":["colnames.csv"]}%
```

One of these mapping names -- `current`, `future`, or simply `colnames` -- must be passed to the command that runs OptiPass so it knows which passability values to use.

## `mapinfo/P`

The `mapinfo` command retuns a dictionary that tells the client how to display a map in the GUI.

There are two kinds of maps.
The demo project uses a **static map** where the map is an image in PNG format.
The dictionary returned by the `mapinfo` command has the necessary information to diplay the map:

```python
"mapinfo": {
    "map_type": "StaticMap",
    "map_file": "Riverlands.png",
    "map_title": "The Riverlands",
    "map_tools": ["hover"]
}
```

The PNG image is also stored on the server; to fetch the map the client sends a `map` command, described below.

The other kind of map is a **tiled map**.
For this type of map the client connects to a GIS server to create the map.
The Oregon project uses a tiled server, and this is the value passed back to the client that tells it how to display that map:

```python
"mapinfo": {
    "map_type": "TiledMap",
    "map_title": "Oregon Coast",
    "map_tools": ["pan","wheel_zoom","hover","reset"]
}
```

The client uses the `mapinfo` structures to draw a map in its GUI.
When the user clicks a region name, the locations of barriers in that regions are displayed on the map.
Those locations are found in the barrier file, in the columns named `X` and `Y`.

* When a project has a static map, the coordinates are locations (in pixels) on the PNG file.
* For a tiled map, the locations are latitude and longitude; the client passes them to the tile server to fetch the geographic region for the barriers.

## `map/P/F`

The `map` command returns a PNG image to the client.  The arguments are the project name and the name of the image file (which the client learned from an earlier `mapinfo` request).

For example, this is the request a client would send if it's displaying the demo data:

```
http://localhost:8000/map/demo/Riverlands.png
```

## `html/P/F`

The `html` command returns the contents of an HTML file.
The client needs to know the name of the file in advance.

For example, both the demo project and the Oregon project have a help page that explains how to use the GUI for that project.
To get the instructions, the client would send a request with the project name, _e.g._

```
 http://localhost:8000/html/demo/welcome.html
```

## `optipass/P`

The `optipass` command is a request to run OptiPass.
The URL for this command is more complicated than the others.
The project name is specified right after the command name, but after that it expects a series of **query parameters**.

Query parameters appear at the end of the URL, after a question mark.
The format for each parameter is a name, an equal sign, and a value.
When there is more than one parameter the name-value pairs are separated by an ampersand.

Here is a partial example, a request to run OptiPass using the demo project, a target named T1, and barriers from the region named Red Fork:

```
http://localhost:8000/optipass/demo?targets=T1&regions=Red+Fork
```

Note that the project name is specified the same way as it is in the other commands, before the question mark (it's a **path parameter**).
Note also there are no spaces in the URL.
The space in the name "Red Fork" is converted to a plus sign.

A parameter can appear more than once.
The server will collect all the values and put them in a list, in the order they appear in the URL.
To run OptiPass with two targets, T1 and T2, the URL would be
```
http://localhost:8000/optipass/demo?targets=T1&targets=T2&...
```

The final URL is going to be very complicated, but fortunately the queries can be generated automatically, for example using a Python library named Requests (which is used by [`op-client`](https://github.com/conery/op-client)).

The complete list of parameters for the `optipass` command are shown in the table below.
If the "Value" colum has "list" it means the argument can be specified multiple times and all values will be collected into a list.

| Argument | Value | Required? | Notes |
| -------- | ----- | --------- | ----- |
| `project` | string | yes | project name (a path parameter) |
| `regions` | list of strings | yes | region names as they appear in the barrier file |
| `targets` | list of strings | yes | 2-letter target IDs |
| `budgets` | list of three integers | yes | starting budget, increment, and count |
| `weights` | list of integers | no | if used there must be one for each target |
| `mapping` | string | no | column name file, _e.g._ `current` or `future` |
| `tempdir` | string | no | directory with existing results (used in testing) |

Note that the server that handles this request must be running on a Windows system with OptiPass installed (but see the note about testing, below).

This request will run OptiPass with data from the demo project, with a single budget of $400,000, using all the gates and both targets, with weight 3 for T1 and weight 1 for T2:
```
> curl 'http://localhost/op/optipass/demo?regions=Trident&regions=Red+Fork&budgets=400000&budgets=0&budgets=1&targets=T1&targets=T2&weights=3&weights=1'
```

The result returned from the server will be a dictionary containing two tables (in the form of CSV files).
The first has one row for each budget, and shows which gates were selected and the potential benefit.
The second has one row for each gate.

The request in the example above is the same one used for Example 4 in the OptiPass manual.  The output should agree with the table in Box 11.


## 
