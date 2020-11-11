#
#
# Display the Image on the Screen
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
    Gst.debug_set_active(True)
    Gst.debug_set_default_threshold(4)
    GObject.threads_init()
    Gst.init(None)

    pipeline = Gst.Pipeline()
    
    source = create_element_or_error("nvarguscamerasrc", "camera-source")
    sink = create_element_or_error("nvoverlaysink", "overlay")

    source.set_property('sensor-id', 0)

    pipeline.add(source)
    pipeline.add(sink)

    source.link(sink)

    loop = GObject.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)

    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except:
        pass

    # Cleanup
    pipeline.set_state(Gst.State.NULL)

if __name__ == "__main__":
    sys.exit(main())
