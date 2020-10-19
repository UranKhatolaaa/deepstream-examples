# 
# The folowing example records the video using a queue
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

    # Create Gst Threads
    tee = create_element_or_error("tee", "tee");
    recording_queue = create_element_or_error("queue", "recording_queue");

    encoder = create_element_or_error('nvv4l2h265enc', 'encoder')
    parser = create_element_or_error('h265parse', 'parser')
    sink = create_element_or_error('filesink', 'sink')

    # Set Element Properties
    source.set_property('sensor-id', 0)
    encoder.set_property('bitrate', 8000000)
    sink.set_property('location', 'prueba.mp4')

    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source, tee, recording_queue, encoder, parser, sink)

    source.link(tee)

    # Link the elements together:
    print("Linking elements in the Pipeline")
    recording_queue.link(encoder)
    encoder.link(parser)
    parser.link(sink)

    # Get pad templates from source
    tee_src_pad_template = tee.get_pad_template("src_%u")

    # Get source to recording queue
    tee_recording_pad = tee.request_pad(tee_src_pad_template, None, None)
    print("Obtained request pad {0} for recording branch".format(tee_recording_pad.get_name()))
    recording_queue_pad = recording_queue.get_static_pad("sink")

    # Link sources
    if (tee_recording_pad.link(recording_queue_pad) != Gst.PadLinkReturn.OK):
        print("ERROR: Tee recording could not be linked")
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
