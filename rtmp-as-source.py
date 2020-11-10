#
# Publish video to Ant Server
#
# gst-launch-1.0 uridecodebin uri=https://media.streamit.link:5443/LiveApp/streams/44c2fc1d83d2ccf2dab09d311aa6da4e.m3u8 ! autovideosink

import argparse
import sys
sys.path.append('../')

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
    pipeline = Gst.Pipeline()
    if not pipeline:
        print("Unable to create Pipeline")
        return False
    
    # Create GST Elements
    source = create_element_or_error("uridecodebin", "uri-source")
    
    # encoder = create_element_or_error("nvv4l2h264enc", "encoder")
    # parser = create_element_or_error("h264parse", "parser")
    sink = create_element_or_error("autovideosink", "sink")

    # if not (source or encoder or parseer or muxer or sink):
    #     return

    # # Set Element Properties
    source.set_property('uri', 'https://media.streamit.link:5443/LiveApp/streams/44c2fc1d83d2ccf2dab09d311aa6da4e.m3u8')
    # source.set_property('do-timestamp', True)
    # sink.set_property('location', 'rtmp://media.streamit.link/LiveApp/streaming-test')

    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    # pipeline.add(encoder)
    # pipeline.add(parser)
    # pipeline.add(muxer)
    pipeline.add(sink)

    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(sink)
    # encoder.link(parser)
    # parser.link(muxer)
    # muxer.link(sink)
    
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
