#!/usr/bin/env python
import rospy
import serial
from std_msgs.msg import String

def callback(msg):
    command = msg.data.strip()
    if command == "":
        rospy.loginfo("Ignoring empty command")
        return
    else:
        rospy.loginfo("Sending to ESP32: {}".format(command))
        ser.write((command + '\n').encode())

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


    pub = rospy.Publisher('arduino_data', String, queue_size=10)
    rospy.Subscriber('motor_command', String, callback)

    rate = rospy.Rate(10) # 10hz
    while not rospy.is_shutdown():
        if ser.in_waiting:
            data = ser.readline().decode('utf-8').strip()
            rospy.loginfo("Received from Arduino: {}".format(data))
            pub.publish(data)

        rate.sleep()

    ser.close

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
