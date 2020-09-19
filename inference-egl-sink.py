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
    source = Gst.ElementFactory.make("nvarguscamerasrc", "camera-source")
    if not source:
        sys.stderr.write(" Unable to create Source")


    # ______________________________
    # Create Nvstreammux instance to form batches from one or more sources.
    print("Creating Streammux")
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    if not streammux:
        sys.stderr.write(" Unable to create NvStreamMux")

    # ______________________________
    # Use nvinfer to run inferencing on camera's output, behaviour of inferencing is set through config file
    print("Creating Primary Inference")
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie")

    # ______________________________
    # Create Convertor Element
    print("Creating Convertor 1")
    convertor = Gst.ElementFactory.make("nvvidconv", "converter-1")
    if not convertor:
        sys.stderr.write(" Unable to create convertor 1")

    # ______________________________
    # Finally render the osd output
    if is_aarch64():
        transform = Gst.ElementFactory.make("nvegltransform", "nvegl-transform")

    # ______________________________
    # Create Overlay Element
    print("Creating EGL Overlay")
    sink = Gst.ElementFactory.make("nveglglessink", "egl-overlay")
    if not sink:
        sys.stderr.write(" Unable to create egl overlay")


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

    convertor.set_property('flip-method', 2)


    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(convertor)
    pipeline.add(sink)
    if is_aarch64():
        pipeline.add(transform)


    sinkpad = streammux.get_request_pad("sink_0")
    if not sinkpad:
        sys.stderr.write(" Unable to get the sink pad of streammux")


    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(streammux)
    streammux.link(pgie)
    pgie.link(convertor)
    if is_aarch64():
        convertor.link(transform)
        transform.link(sink)
    else:
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