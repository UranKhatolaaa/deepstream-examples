#
#
# Display the Image on the Screen using the EGL Sink of Nvidia
#
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
from common.object_detection import osd_sink_pad_buffer_probe

def main():
    
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    # Create Pipeline Element
    pipeline = Gst.Pipeline()
    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline")
        return
    
    # source = create_element_or_error("nvarguscamerasrc", "camera-source")
    # src_caps = create_element_or_error("capsfilter", "source-caps-definition")
    # src_caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), width=(int)1280, height=(int)720, framerate=30/1, format=(string)NV12"))

    streammux = create_element_or_error("nvstreammux", "Stream-muxer")
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    tracker = create_element_or_error("nvtracker", "tracker")
    convertor = Gst.ElementFactory.make("nvvideoconvert", "convertor-1")
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    convertor2 = Gst.ElementFactory.make("nvvidconv", "converter-2")
    transform = create_element_or_error("nvegltransform", "nvegl-transform")
    sink = create_element_or_error("nveglglessink", "egl-overlay")

    # Set Element Properties
    source.set_property('sensor-id', 0)
    source.set_property('bufapi-version', True)
    
    streammux.set_property('live-source', 1)
    streammux.set_property('width', 1280)
    streammux.set_property('height', 720)
    streammux.set_property('num-surfaces-per-frame', 1)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 4000000)

    pgie.set_property('config-file-path', "./nv-inferance-config-files/config_infer_primary_trafficcamnet.txt")

    #Set properties of tracker
    tracker.set_property('tracker-width', 640)
    tracker.set_property('tracker-height', 384)
    tracker.set_property('ll-lib-file', '/opt/nvidia/deepstream/deepstream-5.0/lib/libnvds_nvdcf.so')
    tracker.set_property('gpu-id', 0)
    tracker.set_property('enable-batch-process', 1)
    tracker.set_property('enable-past-frame', 1)
    tracker.set_property('ll-config-file', './tracker_config.yml')

    # Add Elemements to Pipielin
    pipeline.add(source)
    # pipeline.add(src_caps)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(convertor)
    pipeline.add(nvosd)
    pipeline.add(convertor2)
    pipeline.add(transform)
    pipeline.add(sink)

    sinkpad = streammux.get_request_pad("sink_0")
    if not sinkpad:
        sys.stderr.write(" Unable to get the sink pad of streammux")

    # Link the elements together:
    source.link(streammux)
    # src_caps.link(streammux)
    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(convertor)
    convertor.link(nvosd)
    nvosd.link(convertor2)
    convertor2.link(transform)
    transform.link(sink)
    
    # Create an event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)

    #Feed tracker
    tracker_sinkpad = tracker.get_static_pad("sink")
    if not tracker_sinkpad:
        sys.stderr.write(" Unable to get sink pad of nvosd")

    tracker_sinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

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
