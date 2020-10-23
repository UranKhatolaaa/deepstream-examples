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
from common.object_detection import osd_sink_pad_buffer_probe
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
    source = create_element_or_error("nvarguscamerasrc", "camera-source")
    
    streammux = create_element_or_error("nvstreammux", "Stream-muxer")
    pgie = create_element_or_error("nvinfer", "primary-inference")
    convertor = create_element_or_error("nvvideoconvert", "convertor-1")
    nvosd = create_element_or_error("nvdsosd", "onscreendisplay")
    convertor2 = create_element_or_error("nvvideoconvert", "convertor-2")
    caps = create_element_or_error("capsfilter", "filter-convertor-2")
    
    encoder = create_element_or_error("nvv4l2h264enc", "encoder")
    parser = create_element_or_error("h264parse", "parser")
    muxer = create_element_or_error("flvmux", "muxer")
    sink = create_element_or_error("rtmpsink", "sink")

    if not (source or encoder or parseer or muxer or sink):
        # sys.stderr.write("One of the elements could not be created")
        return

    # Set Element Properties
    source.set_property('sensor-id', 0)
    source.set_property('bufapi-version', True)

    encoder.set_property('insert-sps-pps', True)
    encoder.set_property('bitrate', 4000000)
    
    streammux.set_property('live-source', 1)
    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('num-surfaces-per-frame', 1)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 4000000)

    pgie.set_property('config-file-path', "./nv-inferance-config-files/default.txt")
    sink.set_property('location', 'rtmp://media.streamit.link/LiveApp/streaming-test')

    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(convertor)
    pipeline.add(nvosd)
    pipeline.add(convertor2)
    pipeline.add(encoder)
    pipeline.add(parser)
    pipeline.add(muxer)
    pipeline.add(sink)

    sinkpad = streammux.get_request_pad("sink_0")
    if not sinkpad:
        sys.stderr.write(" Unable to get the sink pad of streammux")

    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(streammux)
    streammux.link(pgie)
    pgie.link(convertor)
    convertor.link(nvosd)
    nvosd.link(convertor2)
    convertor2.link(encoder)
    encoder.link(parser)
    parser.link(muxer)
    muxer.link(sink)
    
    # Create an event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)

    print('Create OSD Sink Pad')
    osdsinkpad = nvosd.get_static_pad("sink")
    if not osdsinkpad:
        sys.stderr.write(" Unable to get sink pad of nvosd")

    osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

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
