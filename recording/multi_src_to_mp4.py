# 
# The folowing example records the video of Multiple CSI Camera to separate MP4 File, Encoded h265
#
# The Gstreamer pipeline representation of this code is:
# gst-launch-1.0 nvarguscamerasrc ! nvv4l2h265enc bitrate=8000000 ! h265parse ! filesink location=1280.mp4 -e
#
# 
#                                   IN PROGRESS
#
#
import argparse
import sys
sys.path.append('./')
import datetime
import gi
import os
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.create_element_or_error import create_element_or_error

global folder_name

def main():


    # Define cameras id sensors
    sensors = [0, 1]

    # Create folder where videos will be stored
    folder_name = './recording/storage'
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    # Create Pipeline Element
    print("Creating Pipeline")
    pipeline = Gst.Pipeline()
    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline")

    # Create nvstreammux instance to form batches from one or more sources.
    # Very helpful plugin https://docs.nvidia.com/metropolis/deepstream/5.0DP/plugin-manual/index.html#page/DeepStream%20Plugins%20Development%20Guide/deepstream_plugin_details.3.03.html
    streammux = create_element_or_error("nvstreammux", "stream-muxer")
    pipeline.add(streammux)

    for sensor in sensors:
        stream_folder = folder_name + "/sensor_" + str(sensor)

        if not os.path.isdir(stream_folder):
            os.mkdir(stream_folder)

        source_bin = create_source_bin(sensor)
        if not source_bin:
            sys.stderr.write("Unable to create source bin")
        
        pipeline.add(source_bin)

        padname = "sink_%u" %sensor
        sinkpad = streammux.get_request_pad(padname) 
        if not sinkpad:
            sys.stderr.write("Unable to create sink pad bin")
        srcpad = source_bin.get_static_pad("src")
        if not srcpad:
            sys.stderr.write("Unable to create src pad bin \n")
        srcpad.link(sinkpad)

    streammux.set_property('live-source', 1)
    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('num-surfaces-per-frame', 1)
    streammux.set_property('batch-size', 2)
    streammux.set_property('batched-push-timeout', 4000000)


    # Create Source Element
    # source = create_element_or_error('nvarguscamerasrc', 'camera-source')
    # encoder = create_element_or_error('nvv4l2h265enc', 'encoder')
    # parser = create_element_or_error('h265parse', 'parser')
    # sink = create_element_or_error('filesink', 'sink')

    # # Set Element Properties
    # source.set_property('sensor-id', 0)
    # encoder.set_property('bitrate', 8000000)
    # sink.set_property('location', 'prueba.mp4')

    # # Add Elemements to Pipielin
    # print("Adding elements to Pipeline")
    # pipeline.add(source)
    # pipeline.add(encoder)
    # pipeline.add(parser)
    # pipeline.add(sink)

    # # Link the elements together:
    # print("Linking elements in the Pipeline")
    # source.link(encoder)
    # encoder.link(parser)
    # parser.link(sink)
    

    # # Create an event loop and feed gstreamer bus mesages to it
    # loop = GObject.MainLoop()
    # bus = pipeline.get_bus()
    # bus.add_signal_watch()
    # bus.connect ("message", bus_call, loop)


    # # Start play back and listen to events
    # print("Starting pipeline")
    # pipeline.set_state(Gst.State.PLAYING)

    # try:
    #     loop.run()
    # except:
    #     pass

    # # Cleanup
    # pipeline.set_state(Gst.State.NULL)

def create_source_bin(sensor):
    print("Creating source bin")

    bin_name= "sensor-bin-%02d" %sensor
    print(bin_name)

    nbin = Gst.Bin.new(bin_name)
    if not nbin:
        sys.stderr.write(" Unable to create source bin")

    camera = Gst.ElementFactory.make("nvarguscamerasrc", "camera-csi-bin")
    if not camera:
        sys.stderr.write(" Unable to create uri decode bin \n")

    camera.set_property("sensor-id", sensor)
    # uri_decode_bin.connect("pad-added", cb_newpad,nbin)
    # uri_decode_bin.connect("child-added",decodebin_child_added,nbin)

    # Gst.Bin.add(nbin, uri_decode_bin)
    bin_pad = nbin.add_pad(Gst.GhostPad.new_no_target("src", Gst.PadDirection.SRC))
    if not bin_pad:
        sys.stderr.write(" Failed to add ghost pad in source bin \n")
        return None

    return nbin

if __name__ == "__main__":
    sys.exit(main())
