#!/usr/bin/env python3

import sys
sys.path.append('../')
import gi
import configparser
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from gi.repository import GLib
from ctypes import *
import time
import sys
import math
import platform
from common.is_aarch_64 import is_aarch64
from common.FPS import GETFPS
import numpy as np
import pyds
import cv2
import os
import os.path
from os import path


def cb_newpad(decodebin, decoder_src_pad,data):
    print("In cb_newpad\n")
    caps=decoder_src_pad.get_current_caps()
    gststruct=caps.get_structure(0)
    gstname=gststruct.get_name()
    source_bin=data
    features=caps.get_features(0)

    # Need to check if the pad created by the decodebin is for video and not
    # audio.
    if(gstname.find("video")!=-1):
        # Link the decodebin pad only if decodebin has picked nvidia
        # decoder plugin nvdec_*. We do this by checking if the pad caps contain
        # NVMM memory features.
        if features.contains("memory:NVMM"):
            # Get the source bin ghost pad
            bin_ghost_pad=source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")
        else:
            sys.stderr.write(" Error: Decodebin did not pick nvidia decoder plugin.\n")

def decodebin_child_added(child_proxy,Object,name,user_data):
    print("Decodebin child added:", name, "\n")
    if(name.find("decodebin") != -1):
        Object.connect("child-added",decodebin_child_added,user_data)   
    if(is_aarch64() and name.find("nvv4l2decoder") != -1):
        print("Seting bufapi_version\n")
        Object.set_property("bufapi-version",True)

def create_source_bin(uri):
    nbin = Gst.Bin.new("source-bin-0")

    uri_decode_bin = Gst.ElementFactory.make("uridecodebin", "uri-decode-bin")

    uri_decode_bin.set_property("uri", uri)

    uri_decode_bin.connect("pad-added", cb_newpad,nbin)
    uri_decode_bin.connect("child-added", decodebin_child_added,nbin)

    Gst.Bin.add(nbin, uri_decode_bin)

    bin_pad = nbin.add_pad(Gst.GhostPad.new_no_target("src",Gst.PadDirection.SRC))

    return nbin

def main(args):
    GObject.threads_init()
    Gst.init(None)

    pipeline = Gst.Pipeline()

    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    source_bin = create_source_bin('https://media.streamit.link:5443/LiveApp/streams/test.m3u8')
    transform = Gst.ElementFactory.make("nvegltransform", "nvegl-transform")
    sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")

    streammux.set_property('live-source', True)
    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 4000000)

    sink.set_property("sync", 0)

    pipeline.add(streammux)
    pipeline.add(source_bin)
    pipeline.add(transform)
    pipeline.add(sink)

    sinkpad = streammux.get_request_pad('sink_0') 
    srcpad = source_bin.get_static_pad("src")

    srcpad.link(sinkpad)
    streammux.link(transform)    
    transform.link(sink)

    loop = GObject.MainLoop()

    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except:
        pass
    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
