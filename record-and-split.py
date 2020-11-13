#
# Example of recording videos in chunks
#
# Pipeline Example:
# gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM), width=(int)1280, height=(int)720, format=(string)NV12, framerate=(fraction)30/1' ! nvv4l2h264enc ! h264parse ! splitmuxsink location=video%02d.mkv max-size-time=1000000 muxer-factory=matroskamux muxer-properties="properties,streamable=true"
# splitmuxsink location=video%02d.mkv max-size-time=1000000 muxer-factory=matroskamux muxer-properties="properties,streamable=true"

#
# def on_format_location (self, splitmux, fragment_id, user_data):
#     filename = str(datetime.datetime.utcnow().strftime('%Y-%m-%d %H-%M-%S')) + '.mkv'
#     print(filename)
#     return filename
#
# The folowing example publish the video to ant server and record the video locally using a quees
#
import argparse
import sys
sys.path.append('./../')
import datetime
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.create_element_or_error import create_element_or_error

def __location(splitmux, frag):
    print('Creating new video segment')
    print(datetime.datetime.now())
    return 'v-' + str(datetime.datetime.utcnow()) + '.mkv'

def main():
    
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)
    print(Gst)

    # Create Pipeline Element
    print("Creating Pipeline")
    pipeline = Gst.Pipeline()
    if not pipeline:
        sys.stderr.write("Unable to create Pipeline")
    
    # Create GST Source
    source = create_element_or_error("nvarguscamerasrc", "camera-source")
    caps = Gst.ElementFactory.make("capsfilter", "source-caps")
    caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), width=(int)1280, height=(int)720, format=(string)NV12, framerate=(fraction)30/1"))

    # Create Gst Threads
    tee = create_element_or_error("tee", "tee")
    streaming_queue = create_element_or_error("queue", "streaming_queue")
    recording_queue = create_element_or_error("queue", "recording_queue")
    display_queue = create_element_or_error("queue", "display_queue")

    # Create Gst Elements for Streaming Branch
    s_encoder = create_element_or_error("nvv4l2h264enc", "streaming-encoder")
    s_parser = create_element_or_error("h264parse", "streaming-parser")
    s_muxer = create_element_or_error("flvmux", "streaming-muxer")
    s_sink = create_element_or_error("rtmpsink", "streaming-sink")

    # Create Gst Elements for Recording Branch
    r_encoder = create_element_or_error('nvv4l2h264enc', 'recording-encoder')
    r_parser = create_element_or_error('h264parse', 'recording-parser')
    r_sink = create_element_or_error('splitmuxsink', 'recording-sink')

    # Create Gst Elements for Display Branch
    d_sink = create_element_or_error("nvoverlaysink", "display-sink")

    # Set Source Properties
    source.set_property('sensor-id', 0)
    source.set_property('saturation', 1.2)
    source.set_property('exposurecompensation', 1.2)
    source.set_property('wbmode', 0)

    # Set Streaming Properties
    s_sink.set_property('location', 'rtmp://media.streamit.link/LiveApp/streaming-test')

    # Set Display Properties
    d_sink.set_property('overlay', 1)
    d_sink.set_property('overlay-x', 0)
    d_sink.set_property('overlay-y', 0)
    d_sink.set_property('overlay-w', 640)
    d_sink.set_property('overlay-h', 360)

    # Set Streaming Properties
    five_minutes =  900000000000
    r_sink.set_property('max-size-time', 30000000000)
    r_sink.connect('format-location', __location)

    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(caps)
    pipeline.add(tee)
    pipeline.add(streaming_queue)
    pipeline.add(s_encoder)
    pipeline.add(s_parser)
    pipeline.add(s_muxer)
    pipeline.add(s_sink)
    pipeline.add(recording_queue)
    pipeline.add(r_encoder)
    pipeline.add(r_parser)
    pipeline.add(r_sink)
    pipeline.add(display_queue)
    pipeline.add(d_sink)

    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(caps)
    caps.link(tee)

    # Streaming Queue
    streaming_queue.link(s_encoder)
    s_encoder.link(s_parser)
    s_parser.link(s_muxer)
    s_muxer.link(s_sink)

    # Recording Queue
    recording_queue.link(r_encoder)
    r_encoder.link(r_parser)
    r_parser.link(r_sink)

    # Display Queue
    display_queue.link(d_sink)

    # Get pad templates from source
    tee_src_pad_template = tee.get_pad_template("src_%u")

    # Get source to Streaming Queue
    tee_streaming_pad = tee.request_pad(tee_src_pad_template, None, None)
    streaming_queue_pad = streaming_queue.get_static_pad("sink")

    # Get source to Recording Queue
    tee_recording_pad = tee.request_pad(tee_src_pad_template, None, None)
    recording_queue_pad = recording_queue.get_static_pad("sink")

    # Get source to Display Queue
    tee_display_pad = tee.request_pad(tee_src_pad_template, None, None)
    display_queue_pad = display_queue.get_static_pad("sink")

    # Link sources
    if (tee_streaming_pad.link(streaming_queue_pad) != Gst.PadLinkReturn.OK or tee_recording_pad.link(recording_queue_pad) != Gst.PadLinkReturn.OK or tee_display_pad.link(display_queue_pad) != Gst.PadLinkReturn.OK):
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
