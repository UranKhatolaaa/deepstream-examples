# 
# The folowing example records the video of the CSI Camera to a MP4 File, Encoded h265
#
# The Gstreamer pipeline representation of this code is:
# gst-launch-1.0 nvarguscamerasrc ! nvv4l2h265enc bitrate=8000000 ! h265parse ! filesink location=1280.mp4 -e
#
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
    # Gst.debug_set_active(False)
    # Gst.debug_set_default_threshold(3)

    # Create Pipeline Element
    print("Creating Pipeline")
    pipeline = Gst.Pipeline()
    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline")
    
    # Create Gst Threads
    tee = create_element_or_error("tee", "tee")
    recording_queue = create_element_or_error("queue", "recording_queue")

    # Create Source Element
    source = create_element_or_error('nvarguscamerasrc', 'source')
    caps = create_element_or_error('capsfilter', 'source-capsfilter')
    encoder = create_element_or_error('nvv4l2h265enc', 'encoder')
    parser = create_element_or_error('h265parse', 'parser')
    # demuxer = create_element_or_error('matroskamux', 'matroxdemux')
    sink = create_element_or_error('splitmuxsink', 'sink')

    # Set Element Properties
    source.set_property('sensor-id', 0)
    caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), width=(int)1280, height=(int)720, format=(string)NV12, framerate=(fraction)30/1"))
    sink.set_property('max-size-time', 30000000000)
    sink.set_property('muxer', 'matroskamux')
    sink.connect('format-location', __location)

    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(caps)
    pipeline.add(tee)
    pipeline.add(recording_queue)
    pipeline.add(encoder)
    pipeline.add(parser)
    # pipeline.add(demuxer)
    pipeline.add(sink)

    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(caps)
    caps.link(tee)
    recording_queue.link(encoder)
    encoder.link(parser)
    # parser.link(demuxer)
    parser.link(sink)

     # Get pad templates from source
    tee_src_pad_template = tee.get_pad_template("src_%u")

    # Get source to Recording Queue
    tee_pad = tee.request_pad(tee_src_pad_template, None, None)
    queue_pad = recording_queue.get_static_pad("sink")

    if (tee_pad.link(queue_pad) != Gst.PadLinkReturn.OK):
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

# gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM), width=(int)1280, height=(int)720, format=(string)NV12, framerate=(fraction)30/1' ! nvv4l2h265enc ! h265parse ! matroskamux ! filesink location=test.mkv
# gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM), width=(int)1280, height=(int)720, format=(string)NV12, framerate=(fraction)30/1' ! nvv4l2h265enc ! h265parse ! splitmuxsink muxer=matroskamux location=test.mkv max-size-time=30000000000