Build GStreamer 1.16.2

1. Download the latest version of gstreamer available at:
```
http://gstreamer.freedesktop.org/src/
```
The following are the files you need from version 1.16.2:

- gstreamer-1.16.2.tar.xz
- gst-plugins-base-1.16.2.tar.xz
- gst-plugins-good-1.16.2.tar.xz
- gst-plugins-bad-1.16.2.tar.xz
- gst-plugins-ugly-1.16.2.tar.xz

2. Install needed packages with the following command:
```
sudo apt-get install build-essential dpkg-dev flex bison autotools-dev automake liborc-dev autopoint libtool gtk-doc-tools libgstreamer1.0-dev
 ```

3. In the ~/ directory, create a gst_1.16.2 directory
4. Copy the downloaded tar.xz files to the gst_1.16.2 directory.
5. Uncompress the tar.xz files in the gst_1.16.2 directory.
6. Set the PKG_CONFIG_PATH environment variable with the following command:
```
export PKG_CONFIG_PATH=/home/frank/gst_1.16.2/out/lib/pkgconfig
```
7. Access gstreamer folder to build gstreamer with the following commands:
```
./configure --prefix=/home/ubuntu/gst_1.16.2/out
make
sudo make install
```
8. Build gst-plugins-base-1.16.2 with the following commands:
```
sudo apt-get install libxv-dev libasound2-dev libtheora-dev libogg-dev libvorbis-dev
./configure --prefix=/home/ubuntu/gst_1.16.2/out
make
make install
```
9. Build gst-plugins-good-1.16.2 with the following commands:
```
sudo apt-get install libbz2-dev libv4l-dev libvpx-dev libjack-jackd2-dev libsoup2.4-dev libpulse-dev
./configure --prefix=/home/ubuntu/gst_1.16.2/out
make
make install
```
10. Obtain and build gst-plugins-bad-1.16.2 with the following commands:
```
sudo apt-get install faad libfaad-dev libfaac-dev, libssl-dev
./configure --prefix=/home/ubuntu/gst_1.16.2/out
make
make install
```
11. Obtain and build gst-plugins-ugly-1.16.2 with the following commands:
```
sudo apt-get install libx264-dev libmad0-dev
./configure --prefix=/home/ubuntu/gst_1.16.2/out
make
make install
```
12. Set the LD_LIBRARY_PATH environment variable with the following command:
```
export LD_LIBRARY_PATH=/home/ubuntu/gst_1.16.2/out/lib/
```
13. Copy the nvidia gstreamer-1.0 libraries to the gst_1.16.2 plugin directory using the following command:
```
cd /usr/lib/aarch64-linux-gnu/gstreamer-1.0/
cp libgstnv* libgstomx.so \
 ~/gst_1.16.2/out/lib/gstreamer-1.0/
```
The nvidia gstreamer-1.0 libraries include:
```
libgstnvarguscamera.so
libgstnvcompositor.so
libgstnvdrmvideosink.so
libgstnveglglessink.so
libgstnveglstreamsrc.so
libgstnvegltransform.so
libgstnvivafilter.so
libgstnvjpeg.so
libgstnvtee.so
libgstnvvidconv.so
libgstnvvideo4linux2.so
libgstnvvideocuda.so
libgstnvvideosink.so
libgstnvvideosinks.so
libgstomx.so
```
```
sudo apt-get install libxv-dev libasound2-dev libtheora-dev libogg-dev libvorbis-dev
./configure --prefix=/home/ubuntu/gst_1.16.3/out
make
make install
```