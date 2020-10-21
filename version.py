import argparse
import sys
sys.path.append('./')
import datetime
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.create_element_or_error import create_element_or_error

GObject.threads_init()
Gst.init(None)
