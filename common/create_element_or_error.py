import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

def create_element_or_error(elemntId, name):
    print("Creating Element: " + elemntId)
    element = Gst.ElementFactory.make(elemntId, name)
    if not element:
        print(" Unable to create " + elemntId)
    return element;