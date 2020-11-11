#
# Publish video to Ant Server
#
# gst-launch-1.0 uridecodebin uri=https://media.streamit.link:5443/LiveApp/streams/test.m3u8 ! autovideosink
# gst-launch-1.0 souphttpsrc location=https://media.streamit.link:5443/LiveApp/streams/test.m3u8 ! decodebin ! videoconvert ! nvoverlaysink
# gst-launch-1.0 souphttpsrc location=https://media.streamit.link:5443/LiveApp/streams/test.m3u8 ! hlsdemux ! decodebin ! videoconvert ! nvoverlaysink



import argparse
import sys
sys.path.append('../')

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.create_element_or_error import create_element_or_error

def main():
    
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    # Create Pipeline Element
    pipeline = Gst.Pipeline()
    
    # Create GST Elements
    source = create_element_or_error("souphttpsrc", "source")
    muxer = create_element_or_error("hlsdemux", "decoder")
    decode = create_element_or_error("decodebin", "decoder")
    converter = create_element_or_error("videoconvert", "converter")
    sink = create_element_or_error("nvoverlaysink", "sink")

    # Set Element Properties
    source.set_property('location', 'https://media.streamit.link:5443/LiveApp/streams/test.m3u8')
    # source.set_property('is-live', True)
    # source.set_property('keep-alive', True)

    # Add Elemements to Pipielin
    pipeline.add(source)
    pipeline.add(muxer)
    pipeline.add(decode)
    pipeline.add(converter)
    pipeline.add(sink)

    # Link the elements together:
    source.link(muxer)
    muxer.link(decode)
    decode.link(converter)
    converter.link(sink)
    
    # Create an event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()

    # Start play back and listen to events
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except:
        pass

    # Cleanup
    pipeline.set_state(Gst.State.NULL)

if __name__ == "__main__":
    sys.exit(main())
