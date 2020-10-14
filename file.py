# 
# The folowing example records the video of the CSI Camera to a MP4 File, Encoded h265
#
# The Gstreamer pipeline representation of this code is:
# gst-launch-1.0 nvarguscamerasrc ! nvv4l2h265enc bitrate=8000000 ! h265parse ! filesink location=1280.mp4 -e
#
#
import argparse
import sys
sys.path.append('../')
import datetime
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.create_element_or_error import create_element_or_error

def main():
    
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    # Create Pipeline Element
    print("Creating Pipeline")
    pipeline = Gst.Pipeline()
    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline")
    
    # Create Source Element
    source = create_element_or_error('nvarguscamerasrc', 'camera-source')
    encoder = create_element_or_error('nvv4l2h265enc', 'encoder')
    parser = create_element_or_error('h265parse', 'parser')
    sink = create_element_or_error('filesink', 'sink')

    # Set Element Properties
    source.set_property('sensor-id', 0)
    encoder.set_property('bitrate', 8000000)
    sink.set_property('location', 'prueba.mp4')

    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(encoder)
    pipeline.add(parser)
    pipeline.add(sink)

    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(encoder)
    encoder.link(parser)
    parser.link(sink)
    

    # Create an event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)


    # Start play back and listen to events
    print("Starting pipeline")
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except:
        pass

    # Cleanup
    pipeline.set_state(Gst.State.NULL)

if __name__ == "__main__":
    sys.exit(main())
