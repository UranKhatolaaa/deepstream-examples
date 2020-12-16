#
# Publish video to Ant Server
#
import argparse
import sys
sys.path.append('../')

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.create_element_or_error import create_element_or_error
# gst-launch-1.0 -v filesrc location=../streamit-virtual-edge-appliance/storage/tests/concourse/1.MKV ! matroskademux ! h264parse ! flvmux ! rtmpsink location=rtmp://media.streamit.live/LiveApp/streaming-test
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
    source = create_element_or_error("filesrc", "file-source")
    
    demuxer = create_element_or_error("matroskademux", "demuxer")
    parser = create_element_or_error("h264parse", "parser")
    muxer = create_element_or_error("flvmux", "muxer")
    sink = create_element_or_error("rtmpsink", "sink")

    if not (source or demuxer or parseer or muxer or sink):
        return

    # Set Element Properties
    source.set_property('location', '../streamit-virtual-edge-appliance/storage/tests/concourse/1.MKV')
    sink.set_property('location', 'rtmp://media.streamit.live/LiveApp/stream-test')

    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(demuxer)
    pipeline.add(parser)
    pipeline.add(muxer)
    pipeline.add(sink)

    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(demuxer)
    demuxer.link(parser)
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

