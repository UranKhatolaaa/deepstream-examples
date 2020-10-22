#
#
# Display the Image on the Screen And read the config file from the inference models
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

def main():
    
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)


    # Create Pipeline Element
    print("Creating Pipeline")
    pipeline = Gst.Pipeline()
    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline")
    
    # ______________________________
    # Create Source Element
    print("Creating Source")
    source = create_element_or_error("nvarguscamerasrc", "camera-source")
    streammux = create_element_or_error("nvstreammux", "Stream-muxer")
    pgie = create_element_or_error("nvinfer", "primary-inference")
    convertor = create_element_or_error("nvvidconv", "converter")
    sink = create_element_or_error("nvoverlaysink", "overlay")

    # Set Element Properties
    source.set_property('sensor-id', 0)
    source.set_property('bufapi-version', True)
    
    streammux.set_property('live-source', 1)
    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('num-surfaces-per-frame', 1)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 4000000)

    pgie.set_property('config-file-path', "config.txt")

    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(convertor)
    pipeline.add(sink)


    sinkpad = streammux.get_request_pad("sink_0")
    if not sinkpad:
        sys.stderr.write(" Unable to get the sink pad of streammux")


    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(streammux)
    streammux.link(pgie)
    pgie.link(convertor)
    convertor.link(sink)
    

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
