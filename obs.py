#!/usr/bin/env python3

import argparse
import websocket
import json
import sys

# OBS WebSocket server address
OBS_WEBSOCKET_URL = "ws://localhost:4455"

def on_message(ws, message):
    """
    Handle messages received from the OBS WebSocket.
    For WebSocket 4.x, a successful request has "status": "ok" in the response.
    """
    response = json.loads(message)
    print(f"Received: {response}")

    # Check if it's a response to our request
    if "status" in response:
        if response["status"] == "ok":
            print("Action completed successfully!")
        else:
            error_msg = response.get("error", "Unknown error")
            print(f"Error from OBS: {error_msg}")

    # Close the connection once we receive a response
    ws.close()

def on_error(ws, error):
    """
    Handle any errors in the WebSocket connection.
    """
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    """
    Called when the WebSocket connection is closed.
    """
    print("WebSocket connection closed")

def on_open(ws, request_type):
    """
    Called when the WebSocket connection is opened.
    Immediately sends the relevant OBS request.
    """
    request = {
        "request-type": request_type,
        "message-id": "1"  # unique ID to match the response
    }
    ws.send(json.dumps(request))
    print(f"Sent request: {request_type}")

def main():
    # Define valid actions and their corresponding OBS request-type
    valid_actions = {
        "toggleRecording": "StartStopRecording",
        "toggleReplayBuffer": "StartStopReplayBuffer",
        "saveReplay": "SaveReplayBuffer"
    }

    parser = argparse.ArgumentParser(
        description="Simple OBS control script using OBS WebSocket 4.x"
    )
    parser.add_argument(
        "--action",
        choices=valid_actions.keys(),
        required=True,
        help="Specify the action to perform on OBS"
    )
    args = parser.parse_args()

    # Translate --action to OBS WebSocket 4.x request-type
    request_type = valid_actions[args.action]

    # Create a WebSocket connection and specify handlers
    ws = websocket.WebSocketApp(
        OBS_WEBSOCKET_URL,
        on_open=lambda ws_conn: on_open(ws_conn, request_type),
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    # Run the WebSocket client
    ws.run_forever()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Script terminated by user.")
        sys.exit(0)
