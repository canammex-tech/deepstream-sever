################################################################################
# The MIT License
#
# Copyright (c) 2019-2020, Robert Howell. All rights reserved.
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
import time

from dsl import *

# Filespecs for the Primary GIE
inferConfigFile = '../../test/configs/config_infer_primary_nano.txt'
modelEngineFile = '../../test/models/Primary_Detector_Nano/resnet10.caffemodel_b8_gpu0_fp16.engine'
tracker_config_file = '../../test/configs/iou_config.txt'

TILER_WIDTH = DSL_DEFAULT_STREAMMUX_WIDTH
TILER_HEIGHT = 720

WINDOW_WIDTH = TILER_WIDTH
WINDOW_HEIGHT = TILER_HEIGHT

## 
# Function to be called on XWindow KeyRelease event
## 
def xwindow_key_event_handler(key_string, client_data):
    print('key released = ', key_string)
    if key_string.upper() == 'P':
        
        # if we're able to pause the Pipeline (i.e. it's not already paused)
        if dsl_pipeline_pause('pipeline') == DSL_RETURN_SUCCESS:
        
            # then disable the sink meter from reporting metrics
            dsl_sink_meter_enabled_set('meter-sink', False)
            
    elif key_string.upper() == 'R':
    
        # if we're able to Resume the Pipeline 
        if dsl_pipeline_play('pipeline') == DSL_RETURN_SUCCESS:

            # then re-enable the sink meter to start reporting metrics again
            dsl_sink_meter_enabled_set('meter-sink', True)

    elif key_string.upper() == 'Q' or key_string == '':
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
        
## 
# Meter Sink client callback funtion
## 
def meter_sink_handler(session_avgs, interval_avgs, source_count, client_data):

    print('--------------------------------------------------------')
    for source in range(source_count):
        print('Source: ', source, 'Avg FPS: session  : ', session_avgs[source])
        print('                    interval : ', interval_avgs[source])
    print('\n')
    return True
        

def main(args):

    # Since we're not using args, we can Let DSL initialize GST on first call
    while True:
    
        #
        # New Meter-Sink that will measure the Pipeline's throughput. Our client callback will handle writing the 
        # Avg Session FPS and Avg Interval FPS measurements to the console. The Key-released-handler callback (above)
        # will disable the meter when pausing the Pipeline, and re-enable measurements when the Pipeline is resumed
        # Note: Session averages are reset each time a Meter is disabled and then re-enable.
        retval = dsl_sink_meter_new('meter-sink', interval=1, client_handler=meter_sink_handler, client_data=None)
        if retval != DSL_RETURN_SUCCESS:
            break

        #
        # Create the remaining Pipeline components
        # ... starting with eight URI File Sources
        
        retval = dsl_source_uri_new('Camera 1', "../../test/streams/sample_1080p_h264.mp4", False, 0, 0, 0)
        if retval != DSL_RETURN_SUCCESS:
            break
        dsl_source_uri_new('Camera 2', "../../test/streams/sample_1080p_h264.mp4", False, 0, 0, 0)
        dsl_source_uri_new('Camera 3', "../../test/streams/sample_1080p_h264.mp4", False, 0, 0, 0)
        dsl_source_uri_new('Camera 4', "../../test/streams/sample_1080p_h264.mp4", False, 0, 0, 0)
        dsl_source_uri_new('Camera 5', "../../test/streams/sample_1080p_h264.mp4", False, 0, 0, 0)
        dsl_source_uri_new('Camera 6', "../../test/streams/sample_1080p_h264.mp4", False, 0, 0, 0)
        dsl_source_uri_new('Camera 7', "../../test/streams/sample_1080p_h264.mp4", False, 0, 0, 0)
        dsl_source_uri_new('Camera 8', "../../test/streams/sample_1080p_h264.mp4", False, 0, 0, 0)

        # New Primary GIE using the filespecs above, with interval and Id
        retval = dsl_gie_primary_new('primary-gie', inferConfigFile, modelEngineFile, interval=4)
        if retval != DSL_RETURN_SUCCESS:
            break

        # New KTL Tracker, setting max width and height of input frame
        retval = dsl_tracker_ktl_new('ktl-tracker', 480, 288)
        if retval != DSL_RETURN_SUCCESS:
            break

        # New IOU Tracker, setting max width and height of input frame
        retval = dsl_tracker_iou_new('iou-tracker', tracker_config_file, 480, 288)
        if retval != DSL_RETURN_SUCCESS:
            break

        # New Tiler, setting width and height, use default cols/rows set by source count
        retval = dsl_tiler_new('tiler', TILER_WIDTH, TILER_HEIGHT)
        if retval != DSL_RETURN_SUCCESS:
            break
            
        # New OSD with clock enabled... using default values.
        retval = dsl_osd_new('on-screen-display', False)
        if retval != DSL_RETURN_SUCCESS:
            break

        # New Window Sink, 0 x/y offsets and same dimensions as Tiled Display
        retval = dsl_sink_window_new('window-sink', 0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        if retval != DSL_RETURN_SUCCESS:
            break
            
        # Add all the components to our pipeline
        retval = dsl_pipeline_new_component_add_many('pipeline', 
            ['Camera 1', 'Camera 2', 'Camera 3', 'Camera 4', 'Camera 5', 'Camera 6', 'Camera 7', 'Camera 8',
            'primary-gie', 'ktl-tracker', 'tiler', 'on-screen-display', 'meter-sink', 'window-sink', None])
        if retval != DSL_RETURN_SUCCESS:
            break

        # Add the XWindow event handler functions defined above
        retval = dsl_pipeline_xwindow_key_event_handler_add("pipeline", xwindow_key_event_handler, None)
        if retval != DSL_RETURN_SUCCESS:
            break
        retval = dsl_pipeline_xwindow_delete_event_handler_add("pipeline", xwindow_delete_event_handler, None)
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
        break

    # Print out the final result
    print(dsl_return_value_to_string(retval))

    dsl_pipeline_delete_all()
    dsl_component_delete_all()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
