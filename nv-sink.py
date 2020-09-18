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
    
    # Create Source Element
    print("Creating Source")
    source = Gst.ElementFactory.make("nvarguscamerasrc", "camera-source")
    if not source:
        sys.stderr.write(" Unable to create Source")

    # Create Convertor Element
    print("Creating Convertor")
    convertor = Gst.ElementFactory.make("nvvidconv", "converter")
    if not convertor:
        sys.stderr.write(" Unable to create convertor")


    # Create Overlay Element
    print("Creating Overlay")
    sink = Gst.ElementFactory.make("nvoverlaysink", "overlay")
    if not sink:
        sys.stderr.write(" Unable to create overlay")



    # Set Element Properties
    source.set_property('sensor-id', 0)
    convertor.set_property('flip-method', 2)
    


    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(convertor)
    pipeline.add(sink)


    # Link the elements together:
    # source -> overlaysink
    
    print("Linking elements in the Pipeline")
    source.link(convertor)
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
