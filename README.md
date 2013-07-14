# _watchSOCKET_

watchSOCKET is a dashboard for continuously monitoring the output of unix / linux commands in a web browser updated via WebSockets.
It emulates the _watch_ command - a GNU command-line tool that runs the specified command repeatedly on a time interval.

## Prerequisites

watchSOCKET requires [python version 2.7 or newer](http://www.python.org/download/releases/) and [Tornado](http://www.tornadoweb.org/).
To install tornado:
```
pip install tornado
```

## Download and Running
To download watchSOCKET:
```
git clone https://github.com/jlyoung/watchsocket.git
```

Modify _watchersdict.py_ before use to specify the paths to monitor and the commands to execute on those paths.

To run:
_From server's command line:_
```
python server.py
```
_From web browser, browse to:_
```
http://localhost:8888/static/watchsocket/index.html
```