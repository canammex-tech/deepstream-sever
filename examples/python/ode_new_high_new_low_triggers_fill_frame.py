################################################################################
# The MIT License
#
# Copyright (c) 2021, Prominence AI, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
################################################################################

#!/usr/bin/env python

import sys
sys.path.insert(0, "../../")
from dsl import *

uri_file = "../../test/streams/sample_1080p_h264.mp4"

# Filespecs for the Primary GIE and IOU Trcaker
primary_infer_config_file = '../../test/configs/config_infer_primary_nano.txt'
primary_model_engine_file = '../../test/models/Primary_Detector_Nano/resnet10.caffemodel_b8_gpu0_fp16.engine'
tracker_config_file = '../../test/configs/iou_config.txt'

PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3

TILER_WIDTH = DSL_DEFAULT_STREAMMUX_WIDTH
TILER_HEIGHT = DSL_DEFAULT_STREAMMUX_HEIGHT
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

## 
# Function to be called on XWindow KeyRelease event
## 
def xwindow_key_event_handler(key_string, client_data):
    print('key released = ', key_string)
    if key_string.upper() == 'P':
        dsl_pipeline_pause('pipeline')
    elif key_string.upper() == 'R':
        dsl_pipeline_play('pipeline')
    elif key_string.upper() == 'Q' or key_string == '' or key_string == '':
        dsl_main_loop_quit()
 
## 
# Function to be called on XWindow Delete event
## 
def xwindow_delete_event_handler(client_data):
    print('delete window event')
    dsl_main_loop_quit()

## 
# Function to be called on End-of-Stream (EOS) event
## 
def eos_event_listener(client_data):
    print('Pipeline EOS event')
    dsl_main_loop_quit()

## 
# Function to be called on every change of Pipeline state
## 
def state_change_listener(old_state, new_state, client_data):
    print('previous state = ', old_state, ', new state = ', new_state)
    if new_state == DSL_STATE_PLAYING:
        dsl_pipeline_dump_to_dot('pipeline', "state-playing")

def main(args):

    # Since we're not using args, we can Let DSL initialize GST on first call
    while True:
    
        # This example demonstrates the use of the New-High and New-Low Count Triggers
        # new Object Instances as identified by an IOU Tracker. The frame filled with a 
        # color for a (brief) visual indication on New-High and New-Low object counts,
        # with event data printed to the console for each
        #```````````````````````````````````````````````````````````````````````````````````

        # Create a Format Label Action to remove the Object Label from view
        # Note: the label can be disabled with the OSD API as well. 
        retval = dsl_ode_action_format_label_new('remove-label', 
            font=None, has_bg_color=False, bg_color=None)
        if retval != DSL_RETURN_SUCCESS:
            break
            
        # Create a Format Bounding Box Action to remove the box border from view
        retval = dsl_ode_action_format_bbox_new('remove-border', border_width=0,
            border_color=None, has_bg_color=False, bg_color=None)
        if retval != DSL_RETURN_SUCCESS:
            break

        # Create an Any-Class Occurrence Trigger for our remove label and border actions
        retval = dsl_ode_trigger_occurrence_new('every-occurrence-trigger', source='uri-source-1',
            class_id=DSL_ODE_ANY_CLASS, limit=DSL_ODE_TRIGGER_LIMIT_NONE)
        if retval != DSL_RETURN_SUCCESS:
            break
        retval = dsl_ode_trigger_action_add_many('every-occurrence-trigger', 
            actions=['remove-label', 'remove-border', None])
        if retval != DSL_RETURN_SUCCESS:
            break

        #```````````````````````````````````````````````````````````````````````````````````
        # Create two new RGBA fill colors to fill the frame on new-high and new-low
        retval = dsl_display_type_rgba_color_new('opaque-red', red=1.0, green=0.0, blue=0.0, alpha=0.5)
        if retval != DSL_RETURN_SUCCESS:
            break
            
        retval = dsl_display_type_rgba_color_new('opaque-blue', red=0.0, green=0.0, blue=1.0, alpha=0.5)
        if retval != DSL_RETURN_SUCCESS:
            break
            
        #```````````````````````````````````````````````````````````````````````````````````
        # Create two new Actions to fill the frame, one opaque-red the other opaque-blue.
        retval = dsl_ode_action_fill_frame_new('fill-frame-red', color='opaque-red')
        if retval != DSL_RETURN_SUCCESS:
            break
        retval = dsl_ode_action_fill_frame_new('fill-frame-blue', color='opaque-blue')
        if retval != DSL_RETURN_SUCCESS:
            break

        # And a single action to print the event data to the console, which will be used
        # by both our new-min and new-max Triggers - created next
        retval = dsl_ode_action_print_new('print-data', force_flush=False)
        if retval != DSL_RETURN_SUCCESS:
            break

        #```````````````````````````````````````````````````````````````````````````````````
        # Create two new triggers, one for new high with preset of 5 objects
        # i.e will not trigger until at least 6 objects detected, setting the high-count
        retval = dsl_ode_trigger_new_high_new('new-high-trigger', source='uri-source-1',
            class_id=DSL_ODE_ANY_CLASS, limit=DSL_ODE_TRIGGER_LIMIT_NONE, preset=5)
        if retval != DSL_RETURN_SUCCESS:
            break

        # one for new low with preset of 6 objects i.e will not trigger until fewer than
        # 6 objects detected, setting the low-count
        retval = dsl_ode_trigger_new_low_new('new-low-trigger', source='uri-source-1',
            class_id=DSL_ODE_ANY_CLASS, limit=DSL_ODE_TRIGGER_LIMIT_NONE, preset=6)
        if retval != DSL_RETURN_SUCCESS:
            break

        #```````````````````````````````````````````````````````````````````````````````````
        # Next, we add our Actions to our Triggers
        retval = dsl_ode_trigger_action_add_many('new-high-trigger',
            actions=['fill-frame-red', 'print-data', None])
        if retval != DSL_RETURN_SUCCESS:
            break
        retval = dsl_ode_trigger_action_add_many('new-low-trigger',
            actions=['fill-frame-blue', 'print-data', None])
        if retval != DSL_RETURN_SUCCESS:
            break

        #```````````````````````````````````````````````````````````````````````````````````
        # New ODE Handler to handle all ODE Triggers    
        retval = dsl_pph_ode_new('ode-handler')
        if retval != DSL_RETURN_SUCCESS:
            break
        retval = dsl_pph_ode_trigger_add_many('ode-handler', 
            triggers=['new-high-trigger', 'new-low-trigger', None])
        if retval != DSL_RETURN_SUCCESS:
            break
        
        ####################################################################################
        #
        # Create the remaining Pipeline components
        
        # New URI File Source using the filespec defined above
        retval = dsl_source_uri_new('uri-source-1', uri_file, False, 0, 0, 0)
        if retval != DSL_RETURN_SUCCESS:
            break

        # New Primary GIE using the filespecs above with interval = 0
        retval = dsl_infer_gie_primary_new('primary-gie', 
            primary_infer_config_file, primary_model_engine_file, 1)
        if retval != DSL_RETURN_SUCCESS:
            break

        # New KTL Tracker, setting max width and height of input frame
        retval = dsl_tracker_iou_new('iou-tracker', tracker_config_file, 480, 272)
        if retval != DSL_RETURN_SUCCESS:
            break

        # New Tiled Display, setting width and height, use default cols/rows set by source count
        retval = dsl_tiler_new('tiler', TILER_WIDTH, TILER_HEIGHT)
        if retval != DSL_RETURN_SUCCESS:
            break
 
         # Add our ODE Pad Probe Handler to the Sink pad of the Tiler
        retval = dsl_tiler_pph_add('tiler', handler='ode-handler', pad=DSL_PAD_SINK)
        if retval != DSL_RETURN_SUCCESS:
            break

        # New OSD with clock and text enabled... using default values.
        retval = dsl_osd_new('on-screen-display', True, True)
        if retval != DSL_RETURN_SUCCESS:
            break

        # New Window Sink, 0 x/y offsets and same dimensions as Tiled Display
        retval = dsl_sink_window_new('window-sink', 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        if retval != DSL_RETURN_SUCCESS:
            break

        # Add all the components to our pipeline
        retval = dsl_pipeline_new_component_add_many('pipeline', 
            ['uri-source-1', 'primary-gie', 'iou-tracker', 'tiler', 
            'on-screen-display', 'window-sink', None])
        if retval != DSL_RETURN_SUCCESS:
            break

        # Add the XWindow event handler functions defined above
        retval = dsl_pipeline_xwindow_key_event_handler_add("pipeline", 
            xwindow_key_event_handler, None)
        if retval != DSL_RETURN_SUCCESS:
            break
        retval = dsl_pipeline_xwindow_delete_event_handler_add("pipeline", 
            xwindow_delete_event_handler, None)
        if retval != DSL_RETURN_SUCCESS:
            break

        ## Add the listener callback functions defined above
        retval = dsl_pipeline_state_change_listener_add('pipeline', state_change_listener, None)
        if retval != DSL_RETURN_SUCCESS:
            break
        retval = dsl_pipeline_eos_listener_add('pipeline', eos_event_listener, None)
        if retval != DSL_RETURN_SUCCESS:
            break

        # Play the pipeline
        retval = dsl_pipeline_play('pipeline')
        if retval != DSL_RETURN_SUCCESS:
            break

        dsl_main_loop_run()
        retval = DSL_RETURN_SUCCESS
        break

    # Print out the final result
    print(dsl_return_value_to_string(retval))

    # Cleanup all DSL/GST resources
    dsl_delete_all()
    
if __name__ == '__main__':
    sys.exit(main(sys.argv))
