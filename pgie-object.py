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
        sys.stderr.write(" Unable to create Pipeline")
    
    # ______________________________
    # Create Source Element
    print("Creating Source")
    source = Gst.ElementFactory.make("nvarguscamerasrc", "camera-source")
    if not source:
        sys.stderr.write(" Unable to create Source")


    # ______________________________
    # Create Nvstreammux instance to form batches from one or more sources.
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    if not streammux:
        sys.stderr.write(" Unable to create NvStreamMux")

    # ______________________________
    # Use nvinfer to run inferencing on camera's output, behaviour of inferencing is set through config file
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie")


    # # ______________________________
    # # Use convertor to convert from NV12 to RGBA as required by nvosd
    # convertor = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    # if not convertor:
    #     sys.stderr.write(" Unable to create convertor 2")

    # # ______________________________
    # # Create OSD to draw on the converted RGBA buffer
    # nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    # if not nvosd:
    #     sys.stderr.write(" Unable to create nvosd")

    # # Create OSD Post Convert
    # nvvidconv_postosd = Gst.ElementFactory.make("nvvideoconvert", "convertor_postosd")
    # if not nvvidconv_postosd:
    #     sys.stderr.write(" Unable to create nvvidconv_postosd")

    # # Create a caps filter
    # caps = Gst.ElementFactory.make("capsfilter", "filter")
    # caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=NV12"))

    # ______________________________
    # Create Convertor Element
    print("Creating Convertor")
    convertor2 = Gst.ElementFactory.make("nvvidconv", "converter_2")
    if not convertor2:
        sys.stderr.write(" Unable to create convertor")


    # ______________________________
    # Create Overlay Element
    print("Creating Overlay")
    sink = Gst.ElementFactory.make("nvoverlaysink", "overlay")
    if not sink:
        sys.stderr.write(" Unable to create overlay")


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

    convertor2.set_property('flip-method', 2)


    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(streammux)
    pipeline.add(pgie)
    # pipeline.add(convertor)
    # pipeline.add(nvosd)
    # pipeline.add(nvvidconv_postosd)
    # pipeline.add(caps)
    pipeline.add(convertor2)
    pipeline.add(sink)


    # sinkpad = streammux.get_request_pad("sink_0")
    # if not sinkpad:
        # sys.stderr.write(" Unable to get the sink pad of streammux")


    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(streammux)
    streammux.link(pgie)
    pgie.link(convertor2)
    # convertor.link(nvosd)
    # nvosd.link(nvvidconv_postosd)
    # nvvidconv_postosd.link(caps)
    # caps.link(convertor2)
    convertor2.link(sink)
    

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
