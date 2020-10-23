#
#
# Stream over RTSP the camera
#
#
import argparse
import sys
sys.path.append('../')

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import GObject, Gst, GstRtspServer
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
    
    source = create_element_or_error("nvarguscamerasrc", "camera-source")
    encoder = create_element_or_error("nvv4l2h265enc", "encoder")
    parser = create_element_or_error("h265parse", "h265-parser")
    rtppay = create_element_or_error("rtph265pay", "rtppay")
    sink = create_element_or_error("udpsink", "udpsink")

    # Set Element Properties
    source.set_property('sensor-id', 0)

    encoder.set_property('insert-sps-pps', True)
    encoder.set_property('bitrate', 4000000)

    rtppay.set_property('pt', 96)
    updsink_port_num = 5400

    sink.set_property('host', '127.0.0.1')
    sink.set_property('port', updsink_port_num)
    sink.set_property('async', False)
    sink.set_property('sync', 1)
    
    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(parser)
    pipeline.add(encoder)
    pipeline.add(rtppay)
    pipeline.add(sink)

    # Link the elements together:
    print("Linking elements in the Pipeline")
    source.link(encoder)
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
    factory.set_launch( "( udpsrc name=pay0 port=%d buffer-size=524288 caps=\"application/x-rtp, media=video, clock-rate=90000, encoding-name=(string)%s, payload=96 \" )" % (updsink_port_num, 'H265'))
    factory.set_shared(True)
    server.get_mount_points().add_factory("/streaming", factory)
    
    print("\n *** DeepStream: Launched RTSP Streaming at rtsp://localhost:%d/streaming ***\n\n" % rtsp_port_num)

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
