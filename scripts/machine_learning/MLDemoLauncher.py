"""
Demo launcher for NNStreamer Demos

Copyright NXP 2021

Author: Michael Pontikes <michael.pontikes_1@nxp.com>
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gio

import glob
import sys
import os
sys.path.append("/home/root/.nxp-demo-experience/scripts/")
import utils

class MLLaunch(Gtk.Window):

    def __init__(self, demo):

        # Initialization
        self.demo = demo
        super().__init__(title=demo)
        self.set_default_size(450, 250)
        self.set_resizable(False)
        os.environ["VIV_VX_CACHE_BINARY_GRAPH_DIR"] = ("/home/root/.cache"
            "/demoexperience")
        os.environ["VIV_VX_ENABLE_CACHE_GRAPH_BINARY"] = "1"

        # Get widget properties
        devices = ["Example Video"]
        for device in glob.glob('/dev/video*'):
            devices.append(device)

        backends_available = ["NPU", "CPU"]

        displays_available = ["Weston"]

        # Create widgets
        main_grid = Gtk.Grid.new()
        device_label = Gtk.Label.new("Source")
        self.device_combo = Gtk.ComboBoxText()
        backend_label = Gtk.Label.new("Backend")
        self.backend_combo = Gtk.ComboBoxText()
        display_label = Gtk.Label.new("Display")
        self.display_combo = Gtk.ComboBoxText()
        self.launch_button = Gtk.Button.new_with_label("Run")
        header = Gtk.HeaderBar()
        quit_button = Gtk.Button()
        quit_icon = Gio.ThemedIcon(name="application-exit-symbolic")
        quit_image = Gtk.Image.new_from_gicon(quit_icon, Gtk.IconSize.BUTTON)
        separator = Gtk.Separator.new(0)
        time_title_label = Gtk.Label.new("Video Refresh")
        self.time_label = Gtk.Label.new("--.-- ms")
        self.fps_label = Gtk.Label.new("-- FPS")
        inference_title_label = Gtk.Label.new("Inference Time")
        self.inference_label = Gtk.Label.new("--.-- ms")
        self.ips_label = Gtk.Label.new("-- IPS")

        # Organize widgets
        self.add(main_grid)
        self.set_titlebar(header)
        
        quit_button.add(quit_image)
        header.pack_end(quit_button)

        main_grid.set_row_spacing(10)
        main_grid.set_border_width(10)
   
        main_grid.attach(device_label, 0, 1, 2, 1)
        device_label.set_hexpand(True)
        main_grid.attach(backend_label, 0, 2, 2, 1)
        main_grid.attach(display_label, 0, 3, 2, 1)
        
        main_grid.attach(self.device_combo, 2, 1, 2, 1)
        self.device_combo.set_hexpand(True)
        main_grid.attach(self.backend_combo, 2, 2, 2, 1)
        main_grid.attach(self.display_combo, 2, 3, 2, 1)

        main_grid.attach(self.launch_button, 0, 4, 4, 1)

        main_grid.attach(separator, 0, 5, 4, 1)

        main_grid.attach(time_title_label, 0, 6, 2, 1)
        main_grid.attach(self.time_label, 0, 7, 1, 1)
        main_grid.attach(self.fps_label, 1, 7, 1, 1)
        main_grid.attach(inference_title_label, 2, 6, 2, 1)
        main_grid.attach(self.inference_label, 2, 7, 1, 1)
        main_grid.attach(self.ips_label, 3, 7, 1, 1)

        # Configure widgets
        for device in devices:
            self.device_combo.append_text(device)
        for backend in backends_available:
            self.backend_combo.append_text(backend)
        for display in displays_available:
            self.display_combo.append_text(display)

        self.device_combo.set_active(0)
        self.backend_combo.set_active(0)
        self.display_combo.set_active(0)
        self.launch_button.connect("clicked",self.start)
        quit_button.connect("clicked",exit)
        if self.demo == "detect":
            header.set_title("Detection Demo")
        elif self.demo == "id":
            header.set_title("Classification Demo")
        elif self.demo == "pose":
            header.set_title("Pose Demo")
        elif self.demo == "brand":
            header.set_title("Brand Demo")
        else :
            header.set_title("NNStreamer Demo")
        header.set_subtitle("NNStreamer Examples")

    def start(self, button):
        self.update_time = GLib.get_monotonic_time()
        self.launch_button.set_sensitive(False)
        if self.demo == "detect":
            model = utils.download_file(
                "mobilenet_ssd_v2_coco_quant_postprocess.tflite")
            labels = utils.download_file("coco_labels.txt")
            if self.device_combo.get_active_text() == "Example Video":
                device = utils.download_file("detect_example.mov")
            else:
                device = self.device_combo.get_active_text()
            if model == -1 or model == -2 or model == -3:
                error = "mobilenet_ssd_v2_coco_quant_postprocess.tflite"
            elif labels == -1 or labels == -2 or labels == -3:
                error = "coco_labels.txt"
            elif device == -1 or device == -2 or device == -3:
                error = "detect_example.mov"
        if self.demo == "id":
            model = utils.download_file("mobilenet_v1_1.0_224_quant.tflite")
            labels = utils.download_file("1_1.0_224_labels.txt")
            if self.device_combo.get_active_text() == "Example Video":
                device = utils.download_file("id_example.mov")
            else:
                device = self.device_combo.get_active_text()
            if model == -1 or model == -2 or model == -3:
                error = "mobilenet_v1_1.0_224_quant.tflite"
            elif labels == -1 or labels == -2 or labels == -3:
                error = "1_1.0_224_labels.txt"
            elif device == -1 or device == -2 or device == -3:
                error = "id_example.mov"
        if self.demo == "pose":
            model = utils.download_file(
                "posenet_resnet50_uint8_float32_quant.tflite")
            labels = utils.download_file("key_point_labels.txt")
            if self.device_combo.get_active_text() == "Example Video":
                device = utils.download_file("pose_example.mov")
            else:
                device = self.device_combo.get_active_text()
            if model == -1 or model == -2 or model == -3:
                error = "posenet_resnet50_uint8_float32_quant.tflite"
            elif labels == -1 or labels == -2 or labels == -3:
                error = "key_point_labels.txt"
            elif device == -1 or device == -2 or device == -3:
                error = "pose_example.mov"
        if self.demo == "brand":
            model = utils.download_file("brand_model.tflite")
            labels = utils.download_file("brand_labels.txt")
            if self.device_combo.get_active_text() == "Example Video":
                device = utils.download_file("brand_example.mov")
            else:
                device = self.device_combo.get_active_text()
            if model == -1 or model == -2 or model == -3:
                error = "brand_model.tflite"
            elif labels == -1 or labels == -2 or labels == -3:
                error = "brand_labels.txt"
            elif device == -1 or device == -2 or device == -3:
                error = "brand_example.mov"
        if (model == -1 or labels == -1 or device == -1):
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CANCEL,
                text="Cannot find files! The file that you requested" +
                " does not have any metadata that is related to it. " +
                "Please see /home/root/.nxp-demo-experience/downloads.txt" +
                " to see if the requested file exists! \n \n Cannot find:" +
                error)
            dialog.run()
            dialog.destroy()
            self.launch_button.set_sensitive(True)
            return
        if (model == -2 or labels == -2 or device == -2):
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CANCEL,
                text="Cannot download files! The URL used to download the" +
                " file cannot be reached. If you are connected to the " +
                "internet, please check the /home/root/.nxp-demo-experience" +
                "/downloads.txt for the URL. For some regions, " +
                "these sites may be blocked. To install these manually," +
                " please go to the file listed above and provide the " +
                "path to the file in \"PATH\" \n \n Cannot download " + error)
            dialog.run()
            dialog.destroy()
            self.launch_button.set_sensitive(True)
            return
        if (model == -3 or labels == -3 or device == -4):
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CANCEL,
                text="Invalid files! The files where not what we expected." +
                "If you are SURE that the files are correct, delete " +
                "the \"SHA\" value in /home/root/.nxp-demo-experience" +
                "/downloads.txt to bypass the SHA check. \n \n Bad SHA for " +
                error)
            dialog.run()
            dialog.destroy()
            self.launch_button.set_sensitive(True)
            return
        if self.demo == "detect":
            import nndetection
            example = nndetection.ObjectDetection(
                device,
                self.backend_combo.get_active_text(),
                model, labels, self.display_combo.get_active_text(),
                self.update_stats)
            example.run()
        if self.demo == "id":
            import nnclassification
            example = nnclassification.NNStreamerExample(
                device,
                self.backend_combo.get_active_text(),
                model, labels, self.display_combo.get_active_text(),
                self.update_stats)
            example.run_example()
        if self.demo == "pose":
            import nnpose 
            example = nnpose.NNStreamerExample(
                device,
                self.backend_combo.get_active_text(),
                model, labels, self.display_combo.get_active_text(),
                self.update_stats)
            example.run_example()
        if self.demo == "brand":
            import nnbrand
            example = nnbrand.NNStreamerExample(
                device,
                self.backend_combo.get_active_text(),
                model, labels, self.display_combo.get_active_text(),
                self.update_stats)
            example.run_example()
        self.launch_button.set_sensitive(True)

    def update_stats(self, time):
        interval_time = (GLib.get_monotonic_time() - self.update_time)/1000000
        if interval_time > 1:
            refresh_time = time.interval_time
            inference_time = time.tensor_filter.get_property("latency")
            if refresh_time != 0 and inference_time != 0:
                self.time_label.set_text(
                    "{:12.2f}".format(refresh_time/1000) + ' ms')
                self.fps_label.set_text(
                    "{:12.2f}".format(1/(refresh_time/1000000)) + ' FPS')
                self.inference_label.set_text(
                    "{:12.2f}".format(inference_time/1000) + ' ms')
                self.ips_label.set_text(
                    "{:12.2f}".format(1/(inference_time/1000000)) + ' FPS')
            self.update_time = GLib.get_monotonic_time()
        return True

if __name__ == "__main__":
    if (
        len(sys.argv) != 2 and sys.argv[1] != "detect"
        and sys.argv[1] != "id" and sys.argv[1] != "pose"):
        print("Demos available: detect, id, pose")
    else:
        win = MLLaunch(sys.argv[1])
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        Gtk.main()

