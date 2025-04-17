#!/usr/bin/env python
import rospy
from sensor_msgs.msg import Joy
from std_msgs.msg import String

def joy_callback(msg):
    throttle = msg.axes[1] # forward/backward on left stick

    # Map throttle value (-1.0 to 1.0) to microsecond PWM range (1000-2000)
    pwm = int(((throttle + 1.0) / 2.0) * 1000 + 1000)

    if throttle > 0.1:
        direction = "FWD"
    elif throttle < -0.1:
        direction = "REV"
    else:
        direction = "STOP"

    command = "{} {}".format(direction, pwm)
    rospy.loginfo("Publishing: {}".format(command))
    pub.publish(command)

rospy.init_node('joy_to_motor', anonymous=True)
pub = rospy.Publisher('motor_command', String, queue_size=10)
rospy.Subscriber('joy', Joy, joy_callback)
rospy.spin()
