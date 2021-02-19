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
from common.create_element_or_error import create_element_or_error
import pyds

PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3

object_counter = {
    PGIE_CLASS_ID_VEHICLE : 0,
    PGIE_CLASS_ID_PERSON : 0,
    PGIE_CLASS_ID_BICYCLE : 0,
    PGIE_CLASS_ID_ROADSIGN : 0
}

def tracker_sink_pad_buffer_probe(pad, info, u_data):
    
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer")
        return

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    frame_list = batch_meta.frame_meta_list

    while frame_list is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(frame_list.data)
        except StopIteration:
            break

        list_of_objects = frame_meta.obj_meta_list

        while list_of_objects is not None:
            
            try:
                object_meta = pyds.NvDsObjectMeta.cast(list_of_objects.data)
                # https://docs.nvidia.com/metropolis/deepstream/5.0DP/python-api/NvDsMeta/NvDsObjectMeta.html
                # print(object_meta.rect_params.top)
                # print(object_meta.rect_params.left)
                # print(object_meta.rect_params.width)
                # print(object_meta.rect_params.height)
                # print(object_meta.class_id)
                # print(object_meta.obj_label)
                # print(object_meta.object_id)

            except StopIteration:
                break

            # object_counter[object_meta.class_id] += 1

            try: 
                list_of_objects = list_of_objects.next
            except StopIteration:
                break

            display_meta=pyds.nvds_acquire_display_meta_from_pool(batch_meta)
            display_meta.num_rects = 1
            py_nvosd_rect_params = display_meta.rect_params[0]
            print('hello')
            # py_nvosd_rect_params.top = object_meta.rect_params.top
            # py_nvosd_rect_params.left = object_meta.rect_params.left
            # py_nvosd_rect_params.width = object_meta.rect_params.width
            # py_nvosd_rect_params.height = object_meta.rect_params.height
            # pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
            print('llego')
        try:
            frame_list = frame_list.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK

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
    src_caps = create_element_or_error("capsfilter", "source-caps-definition")
    src_caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), width=(int)1280, height=(int)720, framerate=30/1, format=(string)NV12"))

    streammux = create_element_or_error("nvstreammux", "Stream-muxer")
    pgie = create_element_or_error("nvinfer", "primary-inference")
    convertor = create_element_or_error("nvvideoconvert", "convertor-1")
    tracker = create_element_or_error("nvtracker", "tracker")
    convertor2 = create_element_or_error("nvvideoconvert", "convertor-2")
    caps = create_element_or_error("capsfilter", "filter-convertor-2")
    
    encoder = create_element_or_error("nvv4l2h264enc", "encoder")
    parser = create_element_or_error("h264parse", "parser")
    muxer = create_element_or_error("flvmux", "muxer")
    sink = create_element_or_error("rtmpsink", "sink")
    

    # Set Element Properties
    source.set_property('sensor-id', 0)
    source.set_property('bufapi-version', True)

    encoder.set_property('insert-sps-pps', True)
    encoder.set_property('bitrate', 4000000)
    
    streammux.set_property('live-source', 1)
    streammux.set_property('width', 1280)
    streammux.set_property('height', 720)
    streammux.set_property('num-surfaces-per-frame', 1)
    streammux.set_property('batch-size', 30)
    streammux.set_property('batched-push-timeout', 25000)

    tracker.set_property('ll-lib-file', '/opt/nvidia/deepstream/deepstream-5.0/lib/libnvds_nvdcf.so')
    tracker.set_property('gpu-id', 0)
    tracker.set_property('enable-batch-process', 1)
    tracker.set_property('ll-config-file', '/opt/nvidia/deepstream/deepstream-5.0/samples/configs/deepstream-app/tracker_config.yml')

    pgie.set_property('config-file-path', "./nv-inferance-config-files/config_infer_primary_facedetectir.txt")
    sink.set_property('location', 'rtmp://media.streamit.live/LiveApp/streaming-test')

    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(src_caps)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(convertor)
    pipeline.add(tracker)
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
    source.link(src_caps)
    src_caps.link(streammux)
    streammux.link(pgie)
    pgie.link(convertor)
    convertor.link(tracker)
    tracker.link(convertor2)
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
    tracker_sinkpad = tracker.get_static_pad("sink")
    if not tracker_sinkpad:
        sys.stderr.write(" Unable to get sink pad of nvosd")

    tracker_sinkpad.add_probe(Gst.PadProbeType.BUFFER, tracker_sink_pad_buffer_probe, 0)

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
