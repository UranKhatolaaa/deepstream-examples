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
    
    # Create GST Source
    source = create_element_or_error("nvarguscamerasrc", "camera-source")

    # Create Gst Threads
    tee = create_element_or_error("tee", "tee");
    streaming_queue = create_element_or_error("queue", "streaming_queue");

    # Create Gst Elements for Streaming Branch
    s_encoder = create_element_or_error("nvv4l2h264enc", "streaming-encoder")
    s_parser = create_element_or_error("h264parse", "streaming-parser")
    s_muxer = create_element_or_error("flvmux", "streaming-muxer")
    s_sink = create_element_or_error("rtmpsink", "streaming-sink")

    # Set Element Properties
    source.set_property('sensor-id', 0)
    s_sink.set_property('location', 'rtmp://media.streamit.live/LiveApp/streaming-test')


    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source, tee, streaming_queue, s_encoder, s_parser, s_muxer, s_sink)

    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(tee)

    streaming_queue.link(s_encoder)
    s_encoder.link(s_parser)
    s_parser.link(s_muxer)
    s_muxer.link(s_sink)

    # Get pad templates from source
    tee_src_pad_template = tee.get_pad_template("src_%u")

    # Get source to Streaming queue
    tee_streaming_pad = tee.request_pad(tee_src_pad_template, None, None)
    print("Obtained request pad {0} for streaming branch".format(tee_streaming_pad.get_name()))
    streaming_queue_pad = streaming_queue.get_static_pad("sink")

    # Link sources
    if (tee_streaming_pad.link(streaming_queue_pad) != Gst.PadLinkReturn.OK):
        print("ERROR: Tee could not be linked")
        sys.exit(1)
    
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
