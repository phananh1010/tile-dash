# Introduction
In this project, we note several steps to prepare a traditional tile-based DASH streaming framework. The whole framework includes a tile-based DASH server and a streaming client.

Steps including: (1) splitting a 360-degree video from equirectangular format into tiles, (2) hosting a DASH server, and (3) preparing an MP4Client program.

# Step 1: prepare video tiles
We generate tiles from 360 videos in equirectangular format. Three tools are required: ffmpeg, kvazaar, and Mp4Box. [Reference](https://github.com/gpac/gpac/wiki/Tiled-Streaming)

### Step 1a: convert the video into yuv
First, convert video from mp4 to yuv extension using ffmpeg, then re-encode the video such as motion vectors are constrained inside tiles.
```
ffmpeg -i coaster2.mp4 -filter:v fps=27,scale=3840x1920 coaster2.yuv
kvazaar -i coaster2.yuv --input-res 3840x1920 -o coaster2_10x5_1mbps.hvc --tiles 10x5 --slices tiles --mv-constraint frametilemargin --bitrate 1280000 --period 27 --input-fps 27
kvazaar -i coaster2.yuv --input-res 3840x1920 -o coaster2_10x5_1kbps.hvc --tiles 10x5 --slices tiles --mv-constraint frametilemargin --bitrate 1280 --period 27 --input-fps 27
```


### Step 1b: create tiles and mpd file from prepared yuv file
Then, use MP4Box to cut videos into multiple tiles, and create associated mpd file
```
MP4Box -add coaster2_10x5_1mbps.hvc:split_tiles -fps 27 -new coaster2_10x5_1mbps.mp4
MP4Box -add coaster2_10x5_1kbps.hvc:split_tiles -fps 27 -new coaster2_10x5_1kbps.mp4
MP4Box -dash 1000 -rap -frag-rap -profile live -out ./coaster2/coaster2_10x5.mpd coaster2_10x5.mp4
```

# Step 2: start a simple HTTP server
Any HTTP server such as simple python HTTP server, or an apache server is sufficient. Simply copy the mpd files and all the tile files into the same folder.

# Step 3: Access the mpd files through MP4Client.
To play the DASH video using MP4Client, use the following command:
```
MP4Client [URL]
```
For example:
```
MP4Client http://localhost/dash/coaster2_tiled.mpd
```

# Prepare the client: 
In this section, we go into detail how to install MP4Box and MP4Client, which can be used for Step (1) and Step (2). 
This code has been tested for this commit version: 339e7a7363c4a2b31cd29afee1eefe4866c621b3
## Install MP4Box and MP4Client
Follow instruction here: https://github.com/gpac/gpac/wiki/GPAC-Build-Guide-for-Linux
Use the Full GPAC Build options. 

#### NOTE:here are something differs from the instruction above. Make sure you check all of these points to ensure the installation is successful.

Note that `scons` module used by deps_unix use scons built for python2. We need to install python2, then specify the path of scons for .sh file inside deps_unix to scons for python2
```
sudo apt-get install python2
```
Have scons use python2 instead of python3. First, open scons file in sudo mode
```
sudo vi /usr/bin/scons
```
Modify the first line, point to python2
```
#! /usr/bin/python2
```

Go into `./PlatinumSDK/BuildAndCopy2Public.sh` and `./avcap/BuildAndCopy2Public.sh`, change `scons` to `/usr/bin/scons`

Before build the source code, make sure previous code is cleaned up:
```
make clean
make uninstall
make distclean
```

When invoking the `configure` command, remember to use the `--enable-debug` option so that the program can be debugged.
```
./configure --enable-debug
```

NOTE: DO NOT USE GPAC_PUBLIC AS SUGGESTED, USE GPAC AND GO TO DEPS_UNIX AND CHANGE ALL GPAC_PUBLIC TO PUBLIC (IMPORTANT)
Change the term `gpac_public` to `gpac` for all content of `.sh` files in deps_unix. Use this command to quickly search the term `gpac_public`
```
grep -rnw '.' -e 'gpac_public'
```

List of files to be changed:
```
build_all.sh  
build_openhevc_shared.sh  
build_openhevc_static.sh  
build_opensvc_static.sh 
./PlatinumSDK/BuildAndCopy2Public.sh 
./avcap/BuildAndCopy2Public.sh
```



## Modify code
#### Modify the MP4Client source code
Modify the main.c in the following directory: gpac/applications/mp4client
The main entry function of Mp4Client starts from line #1131

Rebuild the .c file by navigating to the child directory, and execute `make` command. There must be a `Makefile` in that directory for the make to work

Run the MP4Client executable file using the following command:
```
./MP4Client http://localhost/dash/coaster2/coaster210x5.mpd
```

or 
```
gpac -gui http://localhost/dash/coaster2/coaster210x5.mpd -graph
```
In the command above, `-gui` parameter must be included to run in DASH mode. `-graph` parameter allows a graph structure showing chains of modules to be printed at the end of the execution.

#### Make a hello message to the client terminal screen
To show a message to the client terminal screen, use the following function:
```
fprintf(stderr, "message\n");
```


## Debug

#### Enable logging while calling MP4Client. 
use `-rti` and `-log-file` option to specify output file. Use `-logs` to specify log level and module to be logged.
For instance, checking log from all module:
```
MP4Client http://localhost/dash/coaster2/coaster210x5.mpd -rti rti.txt -log-file log.txt -logs "error@info"
```
Source for log option: https://helpmanual.io/help/MP4Client/

To debug with gdp, use this command to run the program and also load the test url:
```
gdb --args MP4Client http://localhost/dash/coaster2/coaster210x5.mpd
```

To debug and use mouse to switch viewport, use the following command instead:
```
gdb --args -gui MP4Client http://localhost/dash/coaster2/coaster210x5.mpd#VR
```

To debug with breakpoints in another files, use this command:
```
b <absolute_path>/gpac/src/media_tools/dash_client.c:4309
```


#### Tracked positions to modify the program
Function performing DASH bitrate adaptation
/src/media_tools/dash_client.c      line: 4288      function: dash_do_rate_adaptation

Main entry to the mp4client
/application/mp4client/main.c       line: 1131      function: mp4client_main

Dash module initialization
/src/filters/dmx_dash.c             line: 2007      function: static GF_Err dashdmx_initialize(GF_Filter *filter)

#### Important details regarding tiled-based streaming
Tile data aggregation is run on a separate thread. Code location:
src/media_tools/filters/tileagg.c   line: 265

Check tile stitching section at
src/media_tools/filters/tileagg.c   line: 332       gf_bs_read_int(ctx->bs_r, 1);



