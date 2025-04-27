#!/usr/bin/env python
import rospy
import serial
from std_msgs.msg import String

def main():
    rospy.init_node('motor_listener', anonymous=True)

    port = rospy.get_param('~port', '/dev/ttyUSB0')
    baud = rospy.get_param('~baud', 115200)

    try:
        ser = serial.Serial(port, baud, timeout=1)
        rospy.loginfo("Opened serial port{} at {} baud.".format(port, baud))
    except serial.SerialException as e:
        rospy.logerr("Failed to open serial port {}: {}".format(port, e))
        return

    def callback(msg):
        command = msg.data.strip()
        rospy.loginfo("Sending to ESP32: {}".format(command))
        ser.write((command + '\n').encode())

    rospy.Subscriber('motor_command', String, callback)
    rospy.spin()
    ser.close

if __name__ == '__main__':
    main()
