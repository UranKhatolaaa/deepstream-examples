#
#
# Stream over RTSP the camera with Object Detection
#
# This is a example of the Gstreamer RTSP Server with the Nvidia Infer plugin that loads
# the configuration to run the ai models in the config file.
#
import argparse
import sys
sys.path.append('./')

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import GObject, Gst, GstRtspServer
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.object_detection import osd_sink_pad_buffer_probe

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
    print("Creating Streammux")
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
    print("Creating Convertor 1")
    convertor = Gst.ElementFactory.make("nvvideoconvert", "convertor-1")
    if not convertor:
        sys.stderr.write("Unable to create convertor 1")

    # ______________________________
    # Create OSD to draw on the converted RGBA buffer
    print("Creating OSD")
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    if not nvosd:
        sys.stderr.write("Unable to create nvosd")

    # ______________________________
    # Use convertor to convert from RGBA to I420
    print("Creating Convertor 2")
    convertor2 = Gst.ElementFactory.make("nvvideoconvert", "convertor-2")
    if not convertor2:
        sys.stderr.write("Unable to create convertor 2")

    # Create a caps filter
    caps = Gst.ElementFactory.make("capsfilter", "filter-convertor-2")
    caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))

    # ______________________________
    print("Creating H264 Encoder")
    encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
    if not encoder:
        sys.stderr.write("Unable to create encoder")

    # ______________________________
    # Since the data format in the input file is elementary h264 stream, we need a h264parser
    print("Creating H264Parser")
    parser = Gst.ElementFactory.make("h264parse", "h264-parser")
    if not parser:
        sys.stderr.write("Unable to create h264 parser")

    # ______________________________
    rtppay = Gst.ElementFactory.make("rtph264pay", "rtppay")
    print("Creating H264 rtppay")
    if not rtppay:
        sys.stderr.write("Unable to create rtppay")

    # ______________________________
    # Make the UDP sink
    updsink_port_num = 5400
    sink = Gst.ElementFactory.make("udpsink", "udpsink")
    if not sink:
        sys.stderr.write("Unable to create udpsink")


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

    pgie.set_property('config-file-path', "./config.txt")

    rtppay.set_property('pt', 96)

    sink.set_property('host', '127.0.0.1')
    sink.set_property('port', updsink_port_num)
    sink.set_property('async', False)
    sink.set_property('sync', 1)
    
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
    pipeline.add(rtppay)
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
    parser.link(rtppay)
    rtppay.link(sink)

    # Create an event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)


    # Start streaming
    rtsp_port_num = 8554
    
    server = GstRtspServer.RTSPServer.new()
    server.props.service = "%d" % rtsp_port_num
    server.attach(None)
    
    factory = GstRtspServer.RTSPMediaFactory.new()
    factory.set_launch( "( udpsrc name=pay0 port=%d buffer-size=524288 caps=\"application/x-rtp, media=video, clock-rate=90000, encoding-name=(string)%s, payload=96 \" )" % (updsink_port_num, 'H264'))
    factory.set_shared(True)
    server.get_mount_points().add_factory("/streaming", factory)
    
    print("\n *** DeepStream: Launched RTSP Streaming at rtsp://localhost:%d/streaming ***\n\n" % rtsp_port_num)

    # Lets add probe to get informed of the meta data generated, we add probe to
    # the sink pad of the osd element, since by that time, the buffer would have
    # had got all the metadata.
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
