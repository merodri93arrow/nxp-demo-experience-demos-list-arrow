#!/usr/bin/env python3

"""
NNStreamer example for image classification using tensorflow-lite.

Under GNU Lesser General Public License v2.1

Orginal Author: Jaeyun Jung <jy1210.jung@samsung.com>
Source: https://github.com/nnstreamer/nnstreamer-example
Author: Michael Pontikes <michael.pontikes_1@nxp.com>

From the original source, this was modified to better work with the a
UI and to get better performance on the i.MX 8M Plus
"""

import os
import sys
import logging
import gi
import cairo

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib


class NNStreamerExample:
    def __init__(self, device, backend,
        model, labels, display="Weston", callback=None):
        self.loop = None
        self.pipeline = None
        self.running = False
        self.current_label_index = -1
        self.new_label_index = -1
        self.tflite_model = model
        self.label_path = labels
        self.device = device
        self.backend = backend
        self.display = display
        self.callback = callback
        self.tflite_labels = []
        self.VIDEO_WIDTH = 1920
        self.VIDEO_HEIGHT = 1080
        self.label = "Loading..."
        self.first_frame = True
        self.refresh_time = -1

        if not self.tflite_init():
            raise Exception

        GObject.threads_init()
        Gst.init(None)

    def run_example(self):
        """Init pipeline and run example.

        :return: None
        """

        if self.backend == "CPU":
            backend = "true:cpu"
        elif self.backend == "GPU":
            backend = "true:gpu custom=Delegate:GPU"
        else:
            backend = "true:npu custom=Delegate:NNAPI"

        if self.display == "X11":
            display = "ximagesink name=img_tensor"
        else:
            display = "waylandsink name=img_tensor"

        self.past_time = GLib.get_monotonic_time()
        self.interval_time = -1
        self.label_time = GLib.get_monotonic_time()
       
        if "/dev/video" in self.device:
            pipeline = 'v4l2src name=cam_src device=' + self.device
            pipeline += ' ! imxvideoconvert_g2d ! video/x-raw,width=1920,'
            pipeline += 'height=1080,format=BGRx ! tee name=t_raw'
        else:
            pipeline = 'filesrc location=' + self.device  + ' ! qtdemux'
            pipeline += ' ! vpudec ! tee name=t_raw'
        # main loop
        self.loop = GObject.MainLoop()
        pipeline += ' t_raw. ! queue ! imxvideoconvert_g2d ! cairooverlay '
        pipeline += 'name=tensor_res ! ' + display + ' t_raw. ! '
        pipeline += 'imxvideoconvert_g2d ! '
        pipeline += 'video/x-raw,width=224,height=224,format=RGBA ! '
        pipeline += 'videoconvert ! video/x-raw,format=RGB ! '
        pipeline += 'queue leaky=2 max-size-buffers=2 ! tensor_converter ! '
        pipeline += 'tensor_filter name=tensor_filter framework='
        pipeline += 'tensorflow-lite model=' + self.tflite_model
        pipeline +=  ' accelerator=' + backend
        pipeline += ' silent=FALSE latency=1 ! tensor_sink name=tensor_sink'
        # init pipeline
        
        self.pipeline = Gst.parse_launch(pipeline)

        # bus and message callback
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_bus_message)

        self.tensor_filter = self.pipeline.get_by_name('tensor_filter')

        # tensor sink signal : new data callback
        tensor_sink = self.pipeline.get_by_name('tensor_sink')
        tensor_sink.connect('new-data', self.on_new_data)

        self.reload_time = GLib.get_monotonic_time()
        tensor_res = self.pipeline.get_by_name('tensor_res')
        tensor_res.connect('draw', self.draw_overlay_cb)
        tensor_res.connect('caps-changed', self.prepare_overlay_cb)

        # start pipeline
        self.pipeline.set_state(Gst.State.PLAYING)
        self.running = True

        self.data = -1
        self.data_size = -1
        if self.callback is not None:
            GObject.timeout_add(500, self.callback, self)

        GObject.timeout_add(250, self.update_top_label_index)

        # set window title
        self.set_window_title('img_tensor', 'NNStreamer Classification')

        # run main loop
        self.loop.run()

        # quit when received eos or error message
        self.running = False
        self.pipeline.set_state(Gst.State.NULL)

        bus.remove_signal_watch()

    def on_bus_message(self, bus, message):
        """Callback for message.

        :param bus: pipeline bus
        :param message: message from pipeline
        :return: None
        """
        if message.type == Gst.MessageType.EOS:
            logging.info('received eos message')
            self.loop.quit()
        elif message.type == Gst.MessageType.ERROR:
            error, debug = message.parse_error()
            logging.warning('[error] %s : %s', error.message, debug)
            self.loop.quit()
        elif message.type == Gst.MessageType.WARNING:
            error, debug = message.parse_warning()
            logging.warning('[warning] %s : %s', error.message, debug)
        elif message.type == Gst.MessageType.STREAM_START:
            logging.info('received start message')
        elif message.type == Gst.MessageType.QOS:
            data_format, processed, dropped = message.parse_qos_stats()
            format_str = Gst.Format.get_name(data_format)
            logging.debug('[qos] format[%s] processed[%d] dropped[%d]',
                format_str, processed, dropped)

    def on_new_data(self, sink, buffer):
        """Callback for tensor sink signal.

        :param sink: tensor sink element
        :param buffer: buffer from element
        :return: None
        """
        if self.running:
            new_time = GLib.get_monotonic_time()
            self.interval_time = new_time - self.past_time
            self.past_time = new_time

            for idx in range(buffer.n_memory()):
                mem = buffer.peek_memory(idx)
                result, mapinfo = mem.map(Gst.MapFlags.READ)
                if result:
                    # update label index with max score
                    self.data = mapinfo.data
                    self.data_size = mapinfo.size
                    mem.unmap(mapinfo)

    def set_window_title(self, name, title):
        """Set window title.

        :param name: GstXImageSink element name
        :param title: window title
        :return: None
        """
        element = self.pipeline.get_by_name(name)
        if element is not None:
            pad = element.get_static_pad('sink')
            if pad is not None:
                tags = Gst.TagList.new_empty()
                tags.add_value(Gst.TagMergeMode.APPEND, 'title', title)
                pad.send_event(Gst.Event.new_tag(tags))

    
    # Modified: Changed filepath to point to model and lables on board.
    def tflite_init(self):
        """Check tflite model and load labels.

        :return: True if successfully initialized
        """

        # check model file exists
        if not os.path.exists(self.tflite_model):
            logging.error('cannot find tflite model [%s]', self.tflite_model)
            return False

        # load labels
        label_path = self.label_path
        try:
            with open(label_path, 'r') as label_file:
                for line in label_file.readlines():
                    self.tflite_labels.append(line)
        except FileNotFoundError:
            logging.error('cannot find tflite label [%s]', label_path)
            return False
        del self.tflite_labels[0]

        logging.info(
            'finished to load labels, total [%d]', len(self.tflite_labels))
        return True

    def tflite_get_label(self, index):
        """Get label string with given index.

        :param index: index for label
        :return: label string
        """
        try:
            label = self.tflite_labels[index]
        except IndexError:
            label = ''
        return label

    def update_top_label_index(self):
        """Update tflite label index with max score.

        :param data: array of scores
        :param data_size: data size
        :return: None
        """
        # -1 if failed to get max score index
        self.new_label_index = -1
        if self.data_size == -1:
            return True
        if self.data_size == len(self.tflite_labels):
            scores = [self.data[i] for i in range(self.data_size)]
            max_score = max(scores)
            if max_score > 0:
                self.new_label_index = scores.index(max_score)
                self.label = self.tflite_get_label(self.new_label_index)[:-1]
            
        else:
            logging.error('unexpected data size [%d]', self.data_size)
        return True

    def draw_overlay_cb(self, overlay, context, timestamp, duration):
        width = 1920
        height = 1080
        inference = self.tensor_filter.get_property("latency")
        context.select_font_face(
            'Sans', cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_BOLD)
        context.set_source_rgb(1, 0, 0)
        
        context.set_font_size(20.0)
        context.move_to(50, height-100)
        context.show_text("i.MX NNStreamer Brand Demo")
        if inference == 0:
            context.move_to(50, height-75)
            context.show_text("FPS: ")
            context.move_to(50, height-50)
            context.show_text("IPS: ")
        elif (
            (GLib.get_monotonic_time() - self.reload_time) < 100000
            and self.refresh_time != -1):
            context.move_to(50, height-75)
            context.show_text(
                "FPS: " + "{:12.2f}".format(1/(self.refresh_time/1000000)) +
                " (" + str(self.refresh_time/1000) + " ms)")
            context.move_to(50, height-50)
            context.show_text(
                "IPS: " + "{:12.2f}".format(1/(self.inference/1000000)) +
                " (" + str(self.inference/1000) + " ms)")
        else:
            self.reload_time = GLib.get_monotonic_time()
            self.refresh_time = self.interval_time
            self.inference = self.tensor_filter.get_property("latency")
            context.move_to(50, height-75)
            context.show_text(
                "FPS: " + "{:12.2f}".format(1/(self.refresh_time/1000000)) +
                " (" + str(self.refresh_time/1000) + " ms)")
            context.move_to(50, height-50)
            context.show_text(
                "IPS: " + "{:12.2f}".format(1/(self.inference/1000000)) +
                " (" + str(self.inference/1000) + " ms)")
        context.move_to(50, 100)
        context.set_font_size(30.0)
        context.show_text(self.label)
        if(self.first_frame):
            context.move_to(400, 600)
            context.set_font_size(200.0)
            context.show_text("Loading...")
            self.first_frame = False
        context.set_operator(cairo.Operator.SOURCE)

    def prepare_overlay_cb(self, overlay, caps):
        self.video_caps = caps

if __name__ == '__main__':
    if(len(sys.argv) != 7 and len(sys.argv) != 5):
        print("Usage: python3 nnbrand.py <dev/video*/video file> <NPU/CPU>"+
                " <model file> <label file>")
        exit()
    if(len(sys.argv) == 7):
        example = NNStreamerExample(sys.argv[1],sys.argv[2],sys.argv[3],
            sys.argv[4],sys.argv[5],sys.argv[6])
    if(len(sys.argv) == 5):
        example = NNStreamerExample(sys.argv[1],sys.argv[2],sys.argv[3],
            sys.argv[4])
    example.run_example()
