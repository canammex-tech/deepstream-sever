/*
The MIT License

Copyright (c) 2023-2024, Prominence AI, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in-
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

/* ````````````````````````````````````````````````````````````````````````````````````
# This example demonstrates the use of a Smart-Record Sink and how
# to start a recording session on user/viewer demand - in this case
# by pressing the 'S' key.  The xwindow_key_event_handler calls
# dsl_sink_record_session_start with:
#   start:    the seconds before the current time (i.e.the amount of 
#             cache/history to include.
#   duration: the seconds after the current time (i.e. the amount of 
#             time to record after session start is called).
# Therefore, a total of start-time + duration seconds of data will be recorded.
# 
# **IMPORTANT!** 
# 1. The default max_size for all Smart Recordings is set to 600 seconds. The 
#    recording will be truncated if start + duration > max_size.
#    Use dsl_sink_record_max_size_set to update max_size. 
# 2. The default cache-size for all recordings is set to 60 seconds. The 
#    recording will be truncated if start > cache_size. 
#    Use dsl_sink_record_cache_size_set to update cache_size.
#
# A basic inference Pipeline is used with PGIE, Tracker, OSD, and Window Sink.
#
# DSL Display Types are used to overlay text ("REC") with a red circle to
# indicate when a recording session is in progress. An ODE "Always-Trigger" and an 
# ODE "Add Display Meta Action" are used to add the text's and circle's metadata
# to each frame while the Trigger is enabled. The record_event_listener callback,
# called on both DSL_RECORDING_EVENT_START and DSL_RECORDING_EVENT_END, enables
# and disables the "Always Trigger" according to the event received. 

*/

#include <iostream>
#include <glib.h>

#include "DslApi.h"

/* ````````````````````````````````````````````````````````````````````````````````````#
# The Smart Record Sink is an Encode Sink that supports five (5) encoder types. 
# Two (2) hardware and three (3) software. Use one of the following constants  
# to select the encoder type:
#   - DSL_ENCODER_HW_H264
#   - DSL_ENCODER_HW_H265
#   - DSL_ENCODER_SW_H264
#   - DSL_ENCODER_SW_H265
#   - DSL_ENCODER_SW_MPEG4
#
#  Two container types are supported:
#   - DSL_CONTAINER_MP4
#   - DSL_CONTAINER_MKV
#
#  Set the bitrate to 0 to use the specific Encoder's default rate as follows
#   - HW-H264/H265 = 4000000 
#   - SW-H264/H265 = 2048000 
#   - SW-MPEG      = 200000
*/
// Record Sink configuration 
uint RECORD_SINK_ENCODER   = DSL_ENCODER_HW_H264;
uint RECORD_SINK_CONTAINER = DSL_CONTAINER_MP4;
uint RECORD_SINK_BITRATE   = 0;  // 0 = use the encoders default bitrate.
uint RECORD_SINK_INTERVAL  = 30; // Set the i-frame interval equal to the framerate

// RTSP Source URI for AMCREST Camera    
static const std::wstring amcrest_rtsp_uri = 
    L"rtsp://username:password@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0";

// RTSP Source URI for HIKVISION Camera    
static const std::wstring hikvision_rtsp_uri = 
    L"rtsp://username:password@192.168.1.64:554/Streaming/Channels/101";

// Config and model-engine files - Jetson and dGPU
static const std::wstring primary_infer_config_file(
    L"/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_infer_primary.txt");
static const std::wstring primary_model_engine_file(
    L"/opt/nvidia/deepstream/deepstream/samples/models/Primary_Detector/resnet18_trafficcamnet.etlt_b8_gpu0_int8.engine");

static const std::wstring tracker_config_file(
    L"/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_tracker_IOU.yml");

// Recording parameters - Total recording time = RECORDING_START + RECORDING_DURATION
uint RECORDING_START = 10;
uint RECORDING_DURATION = 20;

int WINDOW_WIDTH = DSL_1K_HD_WIDTH;
int WINDOW_HEIGHT = DSL_1K_HD_HEIGHT;

//
// Function to check if recording is in progress, and to stop
//
void check_stop_recording()
{
    // need to check if there's a recording in progress that needs to be stopped
    boolean is_on;
    dsl_sink_record_is_on_get(L"record-sink", &is_on);
    if (is_on){
        std::cout << "Recording in progress, stoping first." << std::endl;
        dsl_sink_record_session_stop(L"record-sink", true);
    }
}

// 
// Function to be called on XWindow KeyRelease event
// 
void xwindow_key_event_handler(const wchar_t* in_key, void* client_data)
{   
    std::wstring wkey(in_key); 
    std::string key(wkey.begin(), wkey.end());
    std::cout << "key released = " << key << std::endl;
    key = std::toupper(key[0]);
    if(key == "S"){
        dsl_sink_record_session_start(
            L"record-sink", RECORDING_START, RECORDING_DURATION, NULL);
    } else if(key == "P"){
        dsl_pipeline_pause(L"pipeline");
    } else if (key == "R"){
        dsl_pipeline_play(L"pipeline");
    } else if (key == "Q" or key == "" or key == ""){
        check_stop_recording();
        dsl_pipeline_stop(L"pipeline");
        dsl_main_loop_quit();
    }
}

// 
// Function to be called on XWindow Delete event
//
void xwindow_delete_event_handler(void* client_data)
{
    std::cout<<"delete window event"<<std::endl;
    check_stop_recording();
    dsl_pipeline_stop(L"pipeline");
    dsl_main_loop_quit();
}

// 
// Function to be called on End-of-Stream (EOS) event
// 
void eos_event_listener(void* client_data)
{
    std::cout<<"Pipeline EOS event"<<std::endl;
    check_stop_recording();
    dsl_pipeline_stop(L"pipeline");
    dsl_main_loop_quit();
}    

// 
// Function to be called on every change of Pipeline state
// 
void state_change_listener(uint old_state, uint new_state, void* client_data)
{
    std::cout<<"previous state = " << dsl_state_value_to_string(old_state) 
        << ", new state = " << dsl_state_value_to_string(new_state) << std::endl;
}

//    
// Callback function to handle recording session start and stop events
//    
void* record_event_listener(dsl_recording_info* session_info, void* client_data)
{
    DslReturnType retval;

    std::cout << "session_id: " << session_info->session_id << std::endl;
    
    // This callback can be called after the Pipeline has been stopped.
    // Need to get the current state which we'll use below. 
    uint current_state;
    retval = dsl_pipeline_state_get(L"pipeline", &current_state);

    // If we're starting a new recording for this source
    if (session_info->recording_event == DSL_RECORDING_EVENT_START)
    {
        std::cout << "event:      " << "DSL_RECORDING_EVENT_START" << std::endl;

        // Need to make sure the Pipleine is still playing before we 
        // call any of the Trigger and Tiler services below.
        if (current_state != DSL_STATE_PLAYING)
        {
            return NULL;
        }

        // enable the always trigger showing the metadata for "recording in session" 
        uint retval = dsl_ode_trigger_enabled_set(L"rec-on-trigger", true);
        if (retval != DSL_RESULT_SUCCESS)
        {
            std::wcout << L"Enable always trigger failed with error: " 
                << dsl_return_value_to_string(retval) << std::endl;
        }
    }
    // Else, the recording session has ended for this source
    else
    {    
        std::cout << "event:      " << "DSL_RECORDING_EVENT_END" << std::endl;
        std::cout << "filename:   " << session_info->filename << std::endl;
        std::cout << "dirpath:    " << session_info->dirpath << std::endl;
        std::cout << "duration:   " << session_info->duration << std::endl;
        std::cout << "container:  " << session_info->container_type << std::endl;
        std::cout << "width:      " << session_info->width << std::endl;
        std::cout << "height:     " << session_info->height << std::endl;

        // Need to make sure the Pipleine is still playing before we 
        // call any of the Trigger and Tiler services below.
        if (current_state != DSL_STATE_PLAYING)
        {
            return NULL;
        }

        // disable the always trigger showing the metadata for "recording in session" 
        retval = dsl_ode_trigger_enabled_set(L"rec-on-trigger", false);
        if (retval != DSL_RESULT_SUCCESS)
        {
            std::wcout << L"Disable always trigger failed with error: "
                << dsl_return_value_to_string(retval) << std::endl;
        }
    }
    return NULL;
}

int main(int argc, char** argv)
{  
    DslReturnType retval = DSL_RESULT_FAILURE;

    // Since we're not using args, we can Let DSL initialize GST on first call    
    // This construct allows us to use "break" to exit bracketed region below.
    while(true) 
    {    

        // ```````````````````````````````````````````````````````````````````````````
        // Create new RGBA color types for our Display Text and Circle   
        retval = dsl_display_type_rgba_color_custom_new(L"full-red", 
            1.0f, 0.0f, 0.0f, 1.0f);    
        if (retval != DSL_RESULT_SUCCESS) break;

        retval = dsl_display_type_rgba_color_custom_new(L"full-white", 
            1.0f, 1.0f, 1.0f, 1.0f);    
        if (retval != DSL_RESULT_SUCCESS) break;

        retval = dsl_display_type_rgba_color_custom_new(L"opaque-black", 
            0.0f, 0.0f, 0.0f, 0.8f);
        if (retval != DSL_RESULT_SUCCESS) break;

        retval = dsl_display_type_rgba_font_new(L"digital-20-white", 
            L"KacstDigital", 20, L"full-white");    
        if (retval != DSL_RESULT_SUCCESS) break;
        

        // ```````````````````````````````````````````````````````````````````````````
        // Create a new Text type object that will be used to show the recording 
        // in progress    
        retval = dsl_display_type_rgba_text_new(L"rec-text", L"REC    ", 
            10, 30, L"digital-20-white", true, L"opaque-black");
        if (retval != DSL_RESULT_SUCCESS) break;

        // A new RGBA Circle to be used to simulate a red LED light for the recording 
        // in progress.    
        retval = dsl_display_type_rgba_circle_new(L"red-led", 
            94, 52, 8, L"full-red", true, L"full-red");
        if (retval != DSL_RESULT_SUCCESS) break;

        const wchar_t* display_types[] = {L"rec-text", L"red-led", nullptr};
            
        // Create a new Action to display the "recording in-progress" text
        retval = dsl_ode_action_display_meta_add_many_new(L"add-rec-on", display_types);
        if (retval != DSL_RESULT_SUCCESS) break;
            
        // Create an Always Trigger that will trigger on every frame when enabled.
        // We use this trigger to display meta data while the recording is in session.
        // POST_OCCURRENCE_CHECK == after all other triggers are processed first.
        retval = dsl_ode_trigger_always_new(L"rec-on-trigger",     
            DSL_ODE_ANY_SOURCE, DSL_ODE_POST_OCCURRENCE_CHECK);
        if (retval != DSL_RESULT_SUCCESS) break;

        retval = dsl_ode_trigger_action_add(L"rec-on-trigger", L"add-rec-on");
        if (retval != DSL_RESULT_SUCCESS) break;

        // Disable the trigger, to be re-enabled in the recording_event listener callback
        retval = dsl_ode_trigger_enabled_set(L"rec-on-trigger", false);
        if (retval != DSL_RESULT_SUCCESS) break;

        // ##############################################################################

        // New Record-Sink that will buffer encoded video while waiting for the 
        // ODE trigger/action, defined below, to start a new session on first 
        // occurrence of a bicycle. The default 'cache-size' and 'duration' are 
        // defined in DslApi.h Setting the bit rate to 0 to not change from the default.
        retval = dsl_sink_record_new(L"record-sink", L"./", 
            RECORD_SINK_ENCODER, RECORD_SINK_CONTAINER,
            RECORD_SINK_BITRATE, RECORD_SINK_INTERVAL, 
            record_event_listener);
        if (retval != DSL_RESULT_SUCCESS) break;

        // IMPORTANT: Best to set the max-size to the maximum value we 
        // intend to use (see the xwindow_key_event_handler callback above). 
        retval = dsl_sink_record_max_size_set(L"record-sink", 
            RECORDING_START + RECORDING_DURATION);
        if (retval != DSL_RESULT_SUCCESS) break;

        // IMPORTANT: Best to set the default cache-size to the maximum value we 
        // intend to use (see the xwindow_key_event_handler callback above). 
        retval = dsl_sink_record_cache_size_set(L"record-sink", RECORDING_START);
        if (retval != DSL_RESULT_SUCCESS) break;

        // ```````````````````````````````````````````````````````````````````````````

        // Create the remaining Pipeline components
        
        // New RTSP Source: latency = 2000ms, timeout=2s
        retval = dsl_source_rtsp_new(L"rtsp-source",
            hikvision_rtsp_uri.c_str(), DSL_RTP_ALL, 0, 0, 2000, 2);
        if (retval != DSL_RESULT_SUCCESS) break;

        // New Primary GIE using the filespecs defined above, with interval = 4
        retval = dsl_infer_gie_primary_new(L"primary-gie", 
            primary_infer_config_file.c_str(), 
            primary_model_engine_file.c_str(), 4);
        if (retval != DSL_RESULT_SUCCESS) break;

        // New IOU Tracker, setting max width and height of input frame    
        retval = dsl_tracker_new(L"iou-tracker", 
            tracker_config_file.c_str(), 480, 272);
        if (retval != DSL_RESULT_SUCCESS) break;

        // New on-screen-display (OSD) with text, clock and bbox display all enabled.
        retval = dsl_osd_new(L"on-screen-display", true, false, true, false);
        if (retval != DSL_RESULT_SUCCESS) break;
        
        // New ODE Handler for our Trigger
        retval = dsl_pph_ode_new(L"ode-handler");
        if (retval != DSL_RESULT_SUCCESS) break;

        retval = dsl_pph_ode_trigger_add(L"ode-handler", L"rec-on-trigger");
        if (retval != DSL_RESULT_SUCCESS) break;

        // Add the ODE Pad Probe Handler to the Sink Pad of the Tiler    
        retval = dsl_osd_pph_add(L"on-screen-display", L"ode-handler", DSL_PAD_SINK);
        if (retval != DSL_RESULT_SUCCESS) break;

        // New Window Sink, 0 x/y offsets and same dimensions as streammuxer    
        retval = dsl_sink_window_egl_new(L"egl-sink", 
            0, 0, WINDOW_WIDTH, WINDOW_HEIGHT);
        if (retval != DSL_RESULT_SUCCESS) break;

        // Live Source so best to set the Window-Sink's sync enabled setting to false.
        retval = dsl_sink_sync_enabled_set(L"egl-sink", false);
        if (retval != DSL_RESULT_SUCCESS) break;

        // Add the XWindow event handler functions defined above
        retval = dsl_sink_window_key_event_handler_add(L"egl-sink", 
            xwindow_key_event_handler, NULL);
        if (retval != DSL_RESULT_SUCCESS) break;

        retval = dsl_sink_window_delete_event_handler_add(L"egl-sink", 
            xwindow_delete_event_handler, NULL);
        if (retval != DSL_RESULT_SUCCESS) break;
    
        // Add all the components to a new pipeline    
        const wchar_t* cmpts[] = {L"rtsp-source", L"primary-gie", L"iou-tracker", 
            L"on-screen-display", L"egl-sink", L"record-sink", nullptr};
            
        retval = dsl_pipeline_new_component_add_many(L"pipeline", cmpts);    
        if (retval != DSL_RESULT_SUCCESS) break;

        // Add the listener callback functions defined above
        retval = dsl_pipeline_state_change_listener_add(L"pipeline", 
            state_change_listener, nullptr);
        if (retval != DSL_RESULT_SUCCESS) break;

        retval = dsl_pipeline_eos_listener_add(L"pipeline", 
            eos_event_listener, nullptr);
        if (retval != DSL_RESULT_SUCCESS) break;

        // Play the pipeline    
        retval = dsl_pipeline_play(L"pipeline");
        if (retval != DSL_RESULT_SUCCESS) break;

        dsl_main_loop_run();
        retval = DSL_RESULT_SUCCESS;
        break;            
    }

    // Print out the final result
    std::cout << "DSL Return: " <<  dsl_return_value_to_string(retval) << std::endl;

    // Cleanup all DSL/GST resources
    dsl_delete_all();

    std::cout<<"Goodbye!"<<std::endl;  
    return 0;
}

