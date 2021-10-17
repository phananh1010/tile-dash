### list of command to generate tile files for DASH server
ffmpeg -i coaster2.mp4 -s 384x192 -c:v libx264 -b:v 256k -g 120 -an coaster2_384x192_256k.mp4
ffmpeg -i coaster2.mp4 -s 768x384 -c:v libx264 -b:v 512k -g 120 -an coaster2_768x384_512k.mp4
MP4Box -dash 2000 -profile dashavc264:onDemand -mpd-title coaster2-dash -out coaster2.mpd -frag 2000 ./coaster2_768x384_512k.mp4 coaster2_384x192_256k.mp4 
Check the file: http://localhost/dash/coaster2.mpd

Use kvazaar to generate tile
kvazaar -i coaster2.mp4 --input-res 3840x1920 -o coaster2_tiled10x20.hvc --tiles 10x20 --slices tiles --mv-constraint frametilemargin --bitrate 128000 --period 30 --input-fps 30
kvazaar -i coaster2.mp4 --input-res 3840x1920 -o coaster2_tiled5x10.hvc --tiles 5x10 --slices tiles --mv-constraint frametilemargin --bitrate 512000000 --period 30 --input-fps 30
MP4Box -add coaster2_tiled10x20.hvc:split_tiles -fps 30 -new coaster2_tiled10x20.mp4
MP4Box -dash 2000 -rap -mpd-title coaster2-tile-dash -frag-rap -profile dashavc264:onDemand -out coaster2_tiled.mpd coaster2_tiled10x20.mp4 
cp coaster2_* /var/www/html/dash/
MP4Client http://localhost/dash/coaster2_tiled.mpd
