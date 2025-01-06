#!/usr/bin/env python3

import argparse
import websocket
import json
import sys
import time

OBS_WEBSOCKET_URL = "ws://localhost:4455"

def on_message(ws, message):
    """
    Handle all messages received from OBS WebSocket 4.x.
    """
    response = json.loads(message)
    print(f"Received: {response}")

    message_id = response.get("message-id")

    # Handle multi-step "saveReplayEnsured" workflow
    if message_id == "checkStatus":
        # Response to "GetStreamingStatus"
        if response.get("status") == "ok":
            # Check if the replay buffer is active
            replay_active = response.get("replayBufferActive", False)
            if replay_active:
                # Already active, just save the replay
                request = {
                    "request-type": "SaveReplayBuffer",
                    "message-id": "saveReplay"
                }
                ws.send(json.dumps(request))
                print("Replay buffer is active. Sending saveReplay request...")
            else:
                # Otherwise, start the replay buffer first
                request = {
                    "request-type": "StartReplayBuffer",
                    "message-id": "startReplay"
                }
                ws.send(json.dumps(request))
                print("Replay buffer was not active. Sending startReplay request...")
        else:
            print(f"Error from OBS on checkStatus: {response.get('error', 'Unknown error')}")
            ws.close()

    elif message_id == "startReplay":
        # Response to "StartReplayBuffer"
        if response.get("status") == "ok":
            # Give OBS time to fully activate the replay buffer
            time.sleep(1.0)

            # Now attempt to save the replay
            request = {
                "request-type": "SaveReplayBuffer",
                "message-id": "saveReplay"
            }
            ws.send(json.dumps(request))
            print("Replay buffer started (with delay). Sending saveReplay request...")

        else:
            # If the error specifically says the buffer is already active,
            # just proceed with saving the replay
            error_msg = response.get("error", "")
            if error_msg == "replay buffer already active":
                print("Replay buffer is already active; proceeding to save replay.")
                request = {
                    "request-type": "SaveReplayBuffer",
                    "message-id": "saveReplay"
                }
                ws.send(json.dumps(request))
            else:
                print(f"Error from OBS on startReplay: {error_msg}")
                ws.close()

    elif message_id == "saveReplay":
        # Response to "SaveReplayBuffer"
        if response.get("status") == "ok":
            print("Replay saved successfully!")
        else:
            print(f"Error from OBS on saveReplay: {response.get('error', 'Unknown error')}")
        ws.close()

    # Handle single-step actions
    elif message_id == "1":
        if "status" in response:
            if response["status"] == "ok":
                print("Action completed successfully!")
            else:
                error_msg = response.get("error", "Unknown error")
                print(f"Error from OBS: {error_msg}")
        ws.close()

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket connection closed")

def on_open(ws, request_type):
    """
    Called once the WebSocket connection is established.
    """
    if request_type == "saveReplayEnsured":
        # 1) Check replay buffer status
        # 2) If inactive, start it, then save replay
        # 3) If active, just save replay
        request = {
            "request-type": "GetStreamingStatus",
            "message-id": "checkStatus"
        }
        ws.send(json.dumps(request))
        print("Checking replay buffer status...")
    else:
        # Single-step actions
        request = {
            "request-type": request_type,
            "message-id": "1"
        }
        ws.send(json.dumps(request))
        print(f"Sent request: {request_type}")

def main():
    """
    Command-line interface for controlling OBS via WebSocket 4.x.
    """
    valid_actions = {
        "startRecording": "StartRecording",
        "stopRecording": "StopRecording",
        "startReplayBuffer": "StartReplayBuffer",
        "toggleReplayBuffer": "StartStopReplayBuffer",
        "saveReplay": "SaveReplayBuffer",
        "saveReplayEnsured": "saveReplayEnsured"
    }

    parser = argparse.ArgumentParser(
        description="OBS control script (WebSocket 4.x) with multiple actions."
    )
    parser.add_argument(
        "--action",
        choices=valid_actions.keys(),
        required=True,
        help="Which action to perform on OBS."
    )
    args = parser.parse_args()

    request_type = valid_actions[args.action]

    ws = websocket.WebSocketApp(
        OBS_WEBSOCKET_URL,
        on_open=lambda ws_conn: on_open(ws_conn, request_type),
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    try:
        ws.run_forever()
    except KeyboardInterrupt:
        print("Script terminated by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
