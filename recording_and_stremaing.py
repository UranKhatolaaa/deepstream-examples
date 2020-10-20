#
# The folowing example publish the video to ant server and record the video locally using a quees
#
import argparse
import sys
sys.path.append('./')
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
    
    # Create GST Source
    source = create_element_or_error("nvarguscamerasrc", "camera-source")

    # Create Gst Threads
    tee = create_element_or_error("tee", "tee");
    streaming_queue = create_element_or_error("queue", "streaming_queue");
    recording_queue = create_element_or_error("queue", "recording_queue");

    # Create Gst Elements for Streaming Branch
    s_encoder = create_element_or_error("nvv4l2h264enc", "streaming-encoder")
    s_parser = create_element_or_error("h264parse", "streaming-parser")
    s_muxer = create_element_or_error("flvmux", "streaming-muxer")
    s_sink = create_element_or_error("rtmpsink", "streaming-sink")

    # Create Gst Elements for Recording Branch
    r_encoder = create_element_or_error('nvv4l2h265enc', 'encoder')
    r_parser = create_element_or_error('h265parse', 'parser')
    r_sink = create_element_or_error('filesink', 'sink')

    # Set Element Properties
    source.set_property('sensor-id', 0)
    s_sink.set_property('location', 'rtmp://media.streamit.link/LiveApp/streaming-test')
    r_encoder.set_property('bitrate', 8000000)
    r_sink.set_property('location', 'video_' + str(datetime.datetime.utcnow().date()) + '.mp4')

    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source, tee)
    pipeline.add(streaming_queue, s_encoder, s_parser, s_muxer, s_sink)
    pipeline.add(recording_queue, r_encoder, r_parser, r_sink)

    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(tee)

    # Streaming Queue
    streaming_queue.link(s_encoder)
    s_encoder.link(s_parser)
    s_parser.link(s_muxer)
    s_muxer.link(s_sink)

    # Recording Queue
    recording_queue.link(r_encoder)
    r_encoder.link(r_parser)
    r_parser.link(r_sink)

    # Get pad templates from source
    tee_src_pad_template = tee.get_pad_template("src_%u")

    # Get source to Streaming Queue
    tee_streaming_pad = tee.request_pad(tee_src_pad_template, None, None)
    print("Obtained request pad {0} for streaming branch".format(tee_streaming_pad.get_name()))
    streaming_queue_pad = streaming_queue.get_static_pad("sink")

     # Get source to recording Queue
    tee_recording_pad = tee.request_pad(tee_src_pad_template, None, None)
    print("Obtained request pad {0} for recording branch".format(tee_recording_pad.get_name()))
    recording_queue_pad = recording_queue.get_static_pad("sink")

    # Link sources
    if (tee_streaming_pad.link(streaming_queue_pad) != Gst.PadLinkReturn.OK or tee_recording_pad.link(recording_queue_pad) != Gst.PadLinkReturn.OK):
        print("ERROR: Tee streaming could not be linked")
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
