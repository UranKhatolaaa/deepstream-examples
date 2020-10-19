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


    pipeline = Gst.Pipeline()

    # Create Gst Source Element
    source = create_element_or_error("nvarguscamerasrc", "camera-source")

    # Create Gst Threads
    # tee = create_element_or_error("tee", "tee");
    # streaming_queue = create_element_or_error("queue", "streaming_queue");
    # display_queue = create_element_or_error("queue", "display_queue");

    # Create Straming Pipeline
    s_encoder = create_element_or_error("nvv4l2h264enc", "s_encoder")
    s_parser = create_element_or_error("h264parse", "s_parser")
    s_muxer = create_element_or_error("flvmux", "s_muxer")
    s_sink = create_element_or_error("rtmpsink", "s_sink")

    # Create Display Pipeline
    # d_convertor = create_element_or_error("nvvidconv", "d_converter")
    # d_sink = create_element_or_error("nvoverlaysink", "d_sink")

    # Set Element Properties
    source.set_property('sensor-id', 0)
    source.set_property('bufapi-version', True)

    s_sink.set_property('location', 'rtmp://media.streamit.live/LiveApp/streaming-test')

    # Add Streaming Elements to Pipeline
    # pipeline.add(source, tee, streaming_queue, s_encoder, s_parser, s_muxer, s_sink)
    pipeline.add(source, s_encoder, s_parser, s_muxer, s_sink)

    # Add Display Elements to Pipeline
    # pipeline.add(display_queue, d_convertor, d_sink)

    # Link the elements:
    # source.link(tee)

    # Link streaming elements
    # streaming_queue.link(s_encoder)
    source.link(s_encoder)
    s_encoder.link(s_parser)
    s_parser.link(s_muxer)
    s_muxer.link(s_sink)

    # Link display elements
    # display_queue.link(d_convertor)
    # d_convertor.link(d_sink)

    # tee_src_pad_template = tee.get_pad_template("src_%u")

    # Getting the src path for the streaming queue
    # tee_streaming_pad = tee.request_pad(tee_src_pad_template, None, None)
    # print("Obtained request pad {0} for streaming branch".format(tee_streaming_pad.get_name()))
    # streaming_queue_pad = streaming_queue.get_static_pad("sink")

    # Getting the src path for the display queue
    # tee_display_pad = tee.request_pad(tee_src_pad_template, None, None)
    # print("Obtained request pad {0} for display branch".format(tee_display_pad.get_name()))
    # display_queue_pad = display_queue.get_static_pad("sink")

    # if (tee_streaming_pad.link(streaming_queue_pad) != Gst.PadLinkReturn.OK or tee_display_pad.link(display_queue_pad) != Gst.PadLinkReturn.OK):
    # if (tee_display_pad.link(display_queue_pad) != Gst.PadLinkReturn.OK):
        # print("ERROR: Tee could not be linked")
        # sys.exit(1)

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
