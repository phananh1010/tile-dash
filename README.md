# Introduction
In this project, we note several steps to prepare a traditional tile-based DASH streaming framework. The whole framework includes a tile-based DASH server and a streaming client.

Steps including: (1) splitting a 360-degree video from equirectangular format into tiles, (2) hosting a DASH server, and (3) preparing an MP4Client program.

# Step 1: prepare video tiles
We generate tiles from 360 videos in equirectangular format. Two tools are required: ffmpeg, kvazaar, and Mp4Box.

### Step 1a: convert the video into yuv
First, convert video from mp4 to yuv extension using ffmpeg, then re-encode the video such as motion vectors are constrained inside tiles.
```
ffmpeg -i roller.mp4 -filter:v fps=30,scale=3840x1920 roller.yuv
kvazaar -i roller.yuv --input-res 3840x1920 --input-fps 30 --tiles 10x20 -p 30 --mv-constraint frametilemargin --bitrate 50000000 -o roller10x20.h265
```


### Step 1b: create tiles and mpd file from prepared yuv file
Then, use ffmpeg to cut videos into multiple tiles, and use MP4Box to create associated mpd file
```
ffmpeg -i coaster2.mp4 -s 384x192 -c:v libx264 -b:v 256k -g 120 -an coaster2_384x192_256k.mp4
ffmpeg -i coaster2.mp4 -s 768x384 -c:v libx264 -b:v 512k -g 120 -an coaster2_768x384_512k.mp4
MP4Box -dash 2000 -profile dashavc264:onDemand -mpd-title coaster2-dash -out coaster2.mpd -frag 2000 ./coaster2_768x384_512k.mp4 coaster2_384x192_256k.mp4 
```

### NOTE: Here is another way to use kvazaar & MP4Client to generate tile and mpd files, this process has not been verified
```
kvazaar -i coaster2.mp4 --input-res 3840x1920 -o coaster2_tiled10x20.hvc --tiles 10x20 --slices tiles --mv-constraint frametilemargin --bitrate 128000 --period 30 --input-fps 30
kvazaar -i coaster2.mp4 --input-res 3840x1920 -o coaster2_tiled5x10.hvc --tiles 5x10 --slices tiles --mv-constraint frametilemargin --bitrate 512000000 --period 30 --input-fps 30
MP4Box -add coaster2_tiled10x20.hvc:split_tiles -fps 30 -new coaster2_tiled10x20.mp4
MP4Box -dash 2000 -rap -mpd-title coaster2-tile-dash -frag-rap -profile dashavc264:onDemand -out coaster2_tiled.mpd coaster2_tiled10x20.mp4 
cp coaster2_* /var/www/html/dash/
MP4Client http://localhost/dash/coaster2_tiled.mpd
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
In this section, we go into detail how to install MP4Box and MP4Client, which can be used for Step (1) and Step (2)
## Install MP4Box and MP4Client
Follow instruction here: https://github.com/gpac/gpac/wiki/GPAC-Build-Guide-for-Linux
Use the Full GPAC Build options. When invoking the `configure` command, remember to use the `--enable-debug` option so that the program can be debugged.
```
./configure --enable-debug
```

NOTE: DO NOT USE GPAC_PUBLIC AS SUGGESTED, USE GPAC AND GO TO DEPS_UNIX AND CHANGE ALL GPAC_PUBLIC TO PUBLIC (IMPORTANT)
Change gpac_public to gpac in the buid files for deps_unix.

List of files to be changed:
```
build_all.sh  
build_openhevc_shared.sh  
build_openhevc_static.sh  
build_opensvc_static.sh 
./PlatinumSDK/BuildAndCopy2Public.sh 
./avcap/BuildAndCopy2Public.sh
```
Have scons use python2 instead of python3. First, open scons file in sudo mode
```
sudo vi /usr/bin/scons
```
Modify the first line, point to python2
```
#! /usr/bin/python2
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



