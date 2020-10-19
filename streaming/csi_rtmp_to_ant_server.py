#
# Publish video to Ant Server
#
import argparse
import sys
sys.path.append('./')

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call

def main():
    
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    # Create Pipeline Element
    print("Creating Pipeline")
    pipeline = Gst.Pipeline()
    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline")
    
    # Create GST Elements
    source = Gst.ElementFactory.make("nvarguscamerasrc", "camera-source")
    encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
    parser = Gst.ElementFactory.make("h264parse", "parser")
    muxer = Gst.ElementFactory.make("flvmux", "muxer")
    sink = Gst.ElementFactory.make("rtmpsink", "sink")

    if not (source or encoder or parseer or muxer or sink):
        sys.stderr.write("One of the elements could not be created")
        return;

    # Set Element Properties
    source.set_property('sensor-id', 0)
    sink.set_property('location', 'rtmp://media.streamit.live/LiveApp/streaming-test')

    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(encoder)
    pipeline.add(parser)
    pipeline.add(muxer)
    pipeline.add(sink)

    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(encoder)
    encoder.link(parser)
    parser.link(muxer)
    muxer.link(sink)
    
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
