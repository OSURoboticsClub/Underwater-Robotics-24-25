#!/usr/bin/env python
import rospy
import serial
from std_msgs.msg import String

def callback(msg):
    command = msg.data
    rospy.loginfo("Sending to ESP32: {}".format(command))
    ser.write((command + '\n').encode())

if __name__ == '__main__':
    rospy.init_node('motor_listener', anonymous=True)

    ser = serial.Serial('/dev/ttyUSB0', 115220, timeout=1)

    rospy.Subscriber('motor_command', String, callback)
    rospy.spin()
