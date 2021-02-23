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
import pyds

detectedObjectsCount = []

def sink_pad_buffer_probe(pad,info,u_data):
   
    gst_buffer = info.get_buffer()

    if not gst_buffer:
        sys.stderr.write("Unable to get GstBuffer")

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
    #             # https://docs.nvidia.com/metropolis/deepstream/5.0DP/python-api/NvDsMeta/NvDsObjectMeta.html
                if object_meta.object_id not in detectedObjectsCount:
                    detectedObjectsCount.append(object_meta.object_id)
                    print('Detected "' + object_meta.obj_label + '" with ID: ' + str(object_meta.object_id))

            except StopIteration:
                break
            # obj_counter[object_meta.class_id] += 1
            try:
                list_of_objects = list_of_objects.next
            except StopIteration:
                break
        try:
            frame_list = frame_list.next
        except StopIteration:
            break
			
    return Gst.PadProbeReturn.OK

def main():
    print('Tracker Example')
    
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)


    # Create Pipeline Element
    pipeline = Gst.Pipeline()
    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline")
        return
    
    source = create_element_or_error("nvarguscamerasrc", "camera-source")
    streammux = create_element_or_error("nvstreammux", "Stream-muxer")
    pgie = create_element_or_error("nvinfer", "primary-inference")
    tracker = create_element_or_error("nvtracker", "tracker")
    convertor = create_element_or_error("nvvideoconvert", "convertor-1")
    nvosd = create_element_or_error("nvdsosd", "onscreendisplay")
    convertor2 = create_element_or_error("nvvideoconvert", "converter-2")
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

    pgie.set_property('config-file-path', "/opt/nvidia/deepstream/deepstream-5.0/samples/configs/deepstream-app/config_infer_primary.txt")

    tracker.set_property('ll-lib-file', '/opt/nvidia/deepstream/deepstream-5.0/lib/libnvds_nvdcf.so')
    tracker.set_property('gpu-id', 0)
    tracker.set_property('enable-batch-process', 1)
    tracker.set_property('ll-config-file', '/opt/nvidia/deepstream/deepstream-5.0/samples/configs/deepstream-app/tracker_config.yml')


    # Add Elemements to Pipielin
    print("Adding elements to Pipeline")
    pipeline.add(source)
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

    # Link the elements together
    print("Linking elements in the Pipeline")
    source.link(streammux)
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

    print('Create OSD Sink Pad')
    osdsinkpad = nvosd.get_static_pad("sink")
    if not osdsinkpad:
        sys.stderr.write("Unable to get sink pad of nvosd")

    osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, sink_pad_buffer_probe, 0)

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
