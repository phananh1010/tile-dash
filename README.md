# Introduction
In this project, we note several steps to prepare a traditional tile-based DASH streaming framework. The whole framework includes a tile-based DASH server and a streaming client.

Steps including: (1) splitting a 360-degree video from equirectangular format into tiles, (2) hosting a DASH server, and (3) preparing an MP4Client program.

# Step 1: prepare video tiles
We generate tiles from 360 videos in equirectangular format. Three tools are required: ffmpeg, kvazaar, and Mp4Box. [Reference](https://github.com/gpac/gpac/wiki/Tiled-Streaming)

### Step 1a: convert the video into yuv
First, convert video from mp4 to yuv extension using ffmpeg
```
ffmpeg -i coaster2.mp4 -c:v libx265 -b:v 5000M coaster2_500mbps.mp4
ffmpeg -i coaster2.mp4 -c:v libx265 -b:v 5M coaster2_5mbps.mp4

ffmpeg -i coaster2_500mbps.mp4 -filter:v fps=27,scale=3840x1920 coaster2_500mbps.yuv
ffmpeg -i coaster2_5mbps.mp4 -filter:v fps=27,scale=3840x1920 coaster2_5mbps.yuv
```
Then re-encode the video such as motion vectors are constrained inside tiles.

```
kvazaar -i coaster2_500mbps.yuv --input-res 3840x1920 -o coaster2_10x5_500mbps.hvc --tiles 10x5 --slices tiles --mv-constraint frametilemargin --bitrate 500000000 --period 27 --input-fps 27
kvazaar -i coaster2_5mbps.yuv --input-res 3840x1920 -o coaster2_10x5_5mbps.hvc --tiles 10x5 --slices tiles --mv-constraint frametilemargin --bitrate 5000000 --period 27 --input-fps 27
```


### Step 1b: create tiles and mpd file from prepared yuv file
Then, use MP4Box to cut videos into multiple tiles, and create associated mpd file
```
MP4Box -add coaster2_10x5_500mbps.hvc:split_tiles -fps 27 -new coaster2_10x5_500mbps.mp4
MP4Box -add coaster2_10x5_500kbps.hvc:split_tiles -fps 27 -new coaster2_10x5_500kbps.mp4
MP4Box -add coaster2_5mbps_960x480.hvc:split_tiles -fps 27 -new coaster2_5mbps_960x480.mp4
```
Note that after the commands above, of separated tiles are still in the same `mp4` files. To actually generate tile for DASH streaming, use the following command:
```
MP4Box -segment-timeline -dash 1000 -rap -frag-rap -profile live -out ./coaster2/coaster2_10x5.mpd coaster2_10x5_1mbps.mp4 coaster2_10x5_1kbps.mp4
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
sudo apt-get install python2-pip
python -m pip install scons
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


## Construct GPAC pipeline
To establish testing environment, we need to construct a GPAC pipeline, which is a link of multiple filters. 
For instance, this command create a simple tile-based DASH client, the end point is a sink, where packet is consumed, but not rendered:
```
fs = MyFilterSession(0)

#load a source
#f1 = fs.load_src("https://download.tsi.telecom-paristech.fr/gpac/DASH_CONFORMANCE/TelecomParisTech/mp4-onDemand/mp4-onDemand-mpd-V.mpd")
f1 = fs.load_src("http://localhost/dash/coaster2/coaster2_10x5.mpd")
f2 = fs.load("dashin")
f3 = fs.load("tileagg")
#load a sink
f4 = fs.load("inspect:interleave:false:deep:dur=10:buffer=2000")

f2.set_source(f1)
f3.set_source(f2)
f4.set_source(f3)
```

In the code above, `MyFilterSession` is a custom session, where we could implement our own DASH algorithm

