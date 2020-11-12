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


def source_new_pad_added(decodebin, decoder_src_pad, data):
    print("Source Pad Addded")
    caps = decoder_src_pad.get_current_caps()
    gststruct = caps.get_structure(0)
    gstname = gststruct.get_name()
    source_bin = data
    features = caps.get_features(0)

    if(gstname.find("video") != -1):
        # Link the decodebin pad only if decodebin has picked nvidia
        # decoder plugin nvdec_*. We do this by checking if the pad caps contain
        # NVMM memory features.
        if features.contains("memory:NVMM"):
            bin_ghost_pad = source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                sys.stderr.write("Failed to link decoder src pad to source bin ghost pad")
        else:
            sys.stderr.write("Error: Decodebin did not pick nvidia decoder plugin.")

# Create the source
def create_source_bin(uri):
    nbin = Gst.Bin.new("source-bin-0")

    decoder = Gst.ElementFactory.make("uridecodebin", "uri-decode-bin")

    decoder.set_property("uri", uri)

    decoder.connect("pad-added", source_new_pad_added, nbin)

    Gst.Bin.add(nbin, decoder)

    nbin.add_pad(Gst.GhostPad.new_no_target("src", Gst.PadDirection.SRC))

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

    streammux.set_property("nvbuf-memory-type", 4000)

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
