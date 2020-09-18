import argparse
import sys
sys.path.append('../')

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call

def osd_sink_pad_buffer_probe(pad,info,u_data):
    print('Entro...')
    return Gst.PadProbeReturn.OK	

def main():
    
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)


    # Create Pipeline Element
    print("Creating Pipeline")
    pipeline = Gst.Pipeline()
    if not pipeline:
        sys.stderr.write("Unable to create Pipeline")
    
    # ______________________________
    # Create Source Element
    print("Creating Source")
    source = Gst.ElementFactory.make("nvarguscamerasrc", "camera-source")
    if not source:
        sys.stderr.write("Unable to create Source")

    # ______________________________
    # Create Nvstreammux instance to form batches from one or more sources.
    print("Creating Stremmux")
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    if not streammux:
        sys.stderr.write("Unable to create NvStreamMux")

    # ______________________________
    # Use nvinfer to run inferencing on camera's output, behaviour of inferencing is set through config file
    print("Creating Primary Inference")
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write("Unable to create pgie")


    # ______________________________
    # Use convertor to convert from NV12 to RGBA as required by nvosd
    print("Creating Convertor")
    convertor = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    if not convertor:
        sys.stderr.write("Unable to create convertor")

    # Create a caps filter
    caps = Gst.ElementFactory.make("capsfilter", "convertor-filter")
    caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA"))

    # ______________________________
    # Create OSD to draw on the converted RGBA buffer
    print("Creating OSD")
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    if not nvosd:
        sys.stderr.write("Unable to create nvosd")

    # ______________________________
    # Create OSD Post Convert to bring the frames to NV12
    print("Creating Convertor 2")
    convertor2 = Gst.ElementFactory.make("nvvideoconvert", "convertor-2")
    if not convertor2:
        sys.stderr.write("Unable to create convertor 2")

    # Create a caps filter
    caps2 = Gst.ElementFactory.make("capsfilter", "convertor-filter-2")
    caps2.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=NV12"))


    # ______________________________
    # Create Convertor Element to Flip the Image
    print("Creating Convertor 3")
    convertor3 = Gst.ElementFactory.make("nvvidconv", "converter-3")
    if not convertor3:
        sys.stderr.write("Unable to create convertor 3")


    # ______________________________
    # Create Overlay Element
    print("Creating Overlay")
    sink = Gst.ElementFactory.make("nvoverlaysink", "overlay")
    if not sink:
        sys.stderr.write("Unable to create overlay")


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

    # convertor3.set_property('flip-method', 2)


    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(convertor)
    pipeline.add(caps)
    pipeline.add(nvosd)
    pipeline.add(convertor2)
    pipeline.add(caps2)
    pipeline.add(convertor3)
    pipeline.add(sink)


    sinkpad = streammux.get_request_pad("sink_0")
    if not sinkpad:
        sys.stderr.write(" Unable to get the sink pad of streammux")


    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(streammux)
    streammux.link(pgie)
    pgie.link(convertor)
    convertor.link(caps)
    caps.link(nvosd)
    caps.link(convertor2)
    convertor2.link(caps2)
    caps2.link(convertor3)
    convertor3.link(sink)
    

    # Create an event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)

    # Lets add probe to get informed of the meta data generated, we add probe to
    # the sink pad of the osd element, since by that time, the buffer would have
    # had got all the metadata.
    # osdsinkpad = nvosd.get_static_pad("sink")
    # if not osdsinkpad:
        # sys.stderr.write(" Unable to get sink pad of nvosd \n")
    
    # osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

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
