# This work is licensed under the MIT license.
# Copyright (c) 2013-2023 OpenMV LLC. All rights reserved.
# https://github.com/openmv/openmv/blob/master/LICENSE
#
# MJPEG Streaming
#
# This example shows off how to do MJPEG streaming to a FIREFOX webrowser
# Chrome, Firefox and MJpegViewer App on Android have been tested.
# Connect to the IP address/port printed out from ifconfig to view the stream.

import sensor
import time
import network
import socket
import math
SSID = "ERROR 404"  # Network SSID
KEY = "12345678o"  # Network key
HOST = "192.168.111.245"  # Use first available interface
PORT = 8080  # Arbitrary non-privileged port

# Init sensor
sensor.reset()
sensor.set_framesize(sensor.QVGA)
sensor.set_pixformat(sensor.GRAYSCALE)

# Init wlan module and connect to network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, KEY)

while not wlan.isconnected():
    print('Trying to connect to "{:s}"...'.format(SSID))
    time.sleep_ms(1000)

# We should have a valid IP now via DHCP
print("WiFi Connected ", wlan.ifconfig())

# Create server socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

# Bind and listen
s.bind([HOST, PORT])
s.listen(5)

# Set server socket to blocking
s.setblocking(True)


def start_streaming(s):
    print("Waiting for connections..")
    client, addr = s.accept()
    # set client socket timeout to 5s
    client.settimeout(5.0)
    print("Connected to " + addr[0] + ":" + str(addr[1]))

    # Read request from client
    data = client.recv(1024)
    # Should parse client request here

    # Send multipart header
    client.sendall(
        "HTTP/1.1 200 OK\r\n"
        "Server: OpenMV\r\n"
        "Content-Type: multipart/x-mixed-replace;boundary=openmv\r\n"
        "Cache-Control: no-cache\r\n"
        "Pragma: no-cache\r\n\r\n"
    )

    # FPS clock
    clock = time.clock()

    # Start streaming images
    # NOTE: Disable IDE preview to increase streaming FPS.
    while True:
        clock.tick()  # Track elapsed milliseconds between snapshots().
        #frame = sensor.snapshot()
        #frame.rotation_corr(z_rotation=270)

        img = sensor.snapshot()
        for tag in img.find_apriltags():
            # ตรวจสอบว่ามีข้อมูลที่คืนค่ามา
            if tag:
                img.draw_rectangle(tag.rect(), color=(255, 255, 255))  # ใช้ () หลัง rect
                img.draw_cross(tag.cx(), tag.cy(), color=(255, 255, 255))  # ใช้ () หลัง cx และ cy
                print_args = (tag.family(), tag.id(), (180 * tag.rotation()) / math.pi)
                print("Tag Family %s, Tag ID %d, rotation %f (degrees)" % print_args)

        print("FPS:", clock.fps())



        cframe = img.to_jpeg(quality=50, copy=True)
        header = (
            "\r\n--openmv\r\n"
            "Content-Type: image/jpeg\r\n"
            "Content-Length:" + str(cframe.size()) + "\r\n\r\n"
        )
        client.sendall(header)
        client.sendall(cframe)



while True:
    try:
        start_streaming(s)
    except OSError as e:
        print("socket error: ", e)
        # sys.print_exception(e)
