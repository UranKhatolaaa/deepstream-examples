import random
import ssl
import websockets
import asyncio
import os
import sys
import json
import argparse
import json

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
gi.require_version('GstWebRTC', '1.0')
from gi.repository import GstWebRTC
gi.require_version('GstSdp', '1.0')
from gi.repository import GstSdp

# gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! nvv4l2h264enc ! h264parse ! flvmux ! rtmpsink location='rtmp://media.streamit.live/LiveApp/frank-edge live=1' 
# Folowwing pipeline is for CSI Live Camera
# PIPELINE_DESC = '''
#  nvarguscamerasrc ! nvvideoconvert ! queue ! vp8enc deadline=1 ! rtpvp8pay !
#  queue ! application/x-rtp,media=video,encoding-name=VP8,payload=96 ! webrtcbin name=sendrecv 
# '''

# gst-launch-1.0 -v videotestsrc ! omxh264enc ! 'video/x-h264,stream-format=(string)avc' ! flvmux ! rtmpsink location='rtmp://media.streamit.live/LiveApp/bill-edge live=1'
# This one can be used for testing
PIPELINE_DESC = '''
 videotestsrc is-live=true pattern=ball ! videoconvert ! queue ! vp8enc deadline=1 ! rtpvp8pay !
 queue ! application/x-rtp,media=video,encoding-name=VP8,payload=96 ! webrtcbin name=sendrecv 
'''

WEBSOCKET_URL = 'wss://media.streamit.live:5443/LiveApp/websocket?rtmpForward=undefined'

from websockets.version import version as wsv

class WebRTCClient:
    def __init__(self, id):
        self.id = id
        self.conn = None
        self.pipe = None
        self.webrtc = None
        self.peer_id = None
        self.server = WEBSOCKET_URL

    async def connect(self):
        print('Client Connect')
        sslctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        self.conn = await websockets.connect(self.server, ssl=sslctx)
        await self.conn.send('{"command":"publish","streamId":"' + self.id + '", "token":"null","video":true,"audio":false}')

    def send_sdp_offer(self, offer):
        print('Send SDP Offer')
        sdp = offer.sdp.as_text()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.conn.send('{"command":"takeConfiguration", "streamId": "' + self.id + '", "type": "offer", "sdp": "' + sdp +'"}'))
        loop.close()

    def on_offer_created(self, promise, _, __):
        print('Offer Created')
        promise.wait()
        reply = promise.get_reply()
        offer = reply.get_value('offer') #Please check -> https://github.com/centricular/gstwebrtc-demos/issues/42
        promise = Gst.Promise.new()
        self.webrtc.emit('set-local-description', offer, promise)
        promise.interrupt()
        self.send_sdp_offer(offer)

    def on_negotiation_needed(self, element):
        print('Negotiation Needed')
        promise = Gst.Promise.new_with_change_func(self.on_offer_created, element, None)
        element.emit('create-offer', None, promise)

    def send_ice_candidate_message(self, _, mlineindex, candidate):
        data = '{"command":"takeCandidate","streamId":"' + self.id + '","label":'+ str(mlineindex) +', "id":"' + str(mlineindex) +'" "candidate":"' +  str(candidate) +'"}'
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.conn.send(data))
        loop.close()

    def on_incoming_decodebin_stream(self, _, pad):
        print('Incoming Decodebin Stream')
        # if not pad.has_current_caps():
        #     print (pad, 'has no caps, ignoring')
        #     return
        # caps = pad.get_current_caps()
        # assert (len(caps))
        # s = caps[0]
        # name = s.get_name()
        # if name.startswith('video'):
        #     q = Gst.ElementFactory.make('queue')
        #     conv = Gst.ElementFactory.make('videoconvert')
        #     sink = Gst.ElementFactory.make('autovideosink')
        #     self.pipe.add(q, conv, sink)
        #     self.pipe.sync_children_states()
        #     pad.link(q.get_static_pad('sink'))
        #     q.link(conv)
        #     conv.link(sink)
        # elif name.startswith('audio'):
        #     q = Gst.ElementFactory.make('queue')
        #     conv = Gst.ElementFactory.make('audioconvert')
        #     resample = Gst.ElementFactory.make('audioresample')
        #     sink = Gst.ElementFactory.make('autoaudiosink')
        #     self.pipe.add(q, conv, resample, sink)
        #     self.pipe.sync_children_states()
        #     pad.link(q.get_static_pad('sink'))
        #     q.link(conv)
        #     conv.link(resample)
        #     resample.link(sink)

    def on_incoming_stream(self, _, pad):
        print('on_incoming_stream')
        # if pad.direction != Gst.PadDirection.SRC:
        #     return
        # decodebin = Gst.ElementFactory.make('decodebin')
        # decodebin.connect('pad-added', self.on_incoming_decodebin_stream)
        # self.pipe.add(decodebin)
        # decodebin.sync_state_with_parent()
        # self.webrtc.link(decodebin)

    def start_pipeline(self):
        print('Creating WebRTC Pipeline')
        self.pipe = Gst.parse_launch(PIPELINE_DESC)
        self.webrtc = self.pipe.get_by_name('sendrecv')
        self.webrtc.connect('on-negotiation-needed', self.on_negotiation_needed)
        self.webrtc.connect('on-ice-candidate', self.send_ice_candidate_message)
        self.webrtc.connect('pad-added', self.on_incoming_stream)
        self.pipe.set_state(Gst.State.PLAYING)

    def notification(self, data):
        if(data['definition'] == 'publish_started'):
            print('Publish Started')
        else:
            print(data['definition'])

    def take_candidate(self, data):
        if(data['candidate'] and data['label']):
            self.webrtc.emit('add-ice-candidate', data['label'], data['candidate'])

    def take_configuration(self, data):
        assert (self.webrtc)
        assert(data['type'] == 'answer')
        res, sdpmsg = GstSdp.SDPMessage.new()
        GstSdp.sdp_message_parse_buffer(bytes(data['sdp'].encode()), sdpmsg)
        answer = GstWebRTC.WebRTCSessionDescription.new(GstWebRTC.WebRTCSDPType.ANSWER, sdpmsg)
        promise = Gst.Promise.new()
        self.webrtc.emit('set-remote-description', answer, promise)
        promise.interrupt()

    def close_pipeline(self):
        print('Close Pipeline')
        self.pipe.set_state(Gst.State.NULL)
        self.pipe = None
        self.webrtc = None

    async def loop(self):
        print('Inititialized')
        assert self.conn
        async for message in self.conn:

            data = json.loads(message)

            print('Message: ' + data['command']);

            if(data['command'] == 'start'):
                self.start_pipeline()
            elif(data['command'] == 'takeCandidate'):
                self.take_candidate(data)
            elif(data['command'] == 'takeConfiguration'):
                self.take_configuration(data)
            elif(data['command'] == 'notification'):
                self.notification(data)
            elif(data['command'] == 'error'):
                 print('Message: ' + data['definition']);
            
        
        self.close_pipeline()
        return 0

    async def stop(self):
        if self.conn:
            await self.conn.close()
        self.conn = None


def check_plugins():
    needed = ["opus", "vpx", "nice", "webrtc", "dtls", "srtp", "rtp",
              "rtpmanager", "videotestsrc", "audiotestsrc"]
    missing = list(filter(lambda p: Gst.Registry.get().find_plugin(p) is None, needed))
    if len(missing):
        print('Missing gstreamer plugins:', missing)
        return False
    return True


if __name__=='__main__':
    Gst.init(None)
    if not check_plugins():
        sys.exit(1)
    client = WebRTCClient('frank-edge')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.connect())
    res = loop.run_until_complete(client.loop())
    sys.exit(res)