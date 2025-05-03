#!/usr/bin/env python
import rospy
from sensor_msgs.msg import Joy
from std_msgs.msg import String

def clamp(num, min_value, max_value):
    return max(min_value, min(max_value, num))

def to_pwm(cmd):
    cmd = int(((cmd + 1.0) / 2.0) * 1000 + 1000)
    return cmd

old_lfl = 0.0
old_lfr = 0.0
old_lbl = 0.0
old_lbr = 0.0

def joy_callback(msg):
    # msg has an axes array of length 8
    # msg.axes[0] left stick X: 1=left, -1=right
    # msg.axes[1] left stick Y: 1=up, -1=down
    # msg.axes[2] left trigger, 1.0 is unpressed, -1 is fully pressed
    # msg.axes[3] right stick X: 1=left, -1=right
    # msg.axes[4] right stick Y: 1=up, -1=down
    # msg.axes[5] right trigger, 1.0 is unpressed, -1 is fully pressed
    # NOTE: before the triggers have been pressed once, they stay at 0.0
    #       after they've been pressed once they default to 1.0
    # msg.axes[6] left/right on dpad: 1=dpad right, -1=dpad left
    # msg.axes[7] up/down on dpad: 1=dpad up, -1=dpad down
    # 
    # msg also has an buttons array of length 11
    # msg.buttons[0] = A
    # msg.buttons[1] = B
    # msg.buttons[2] = X
    # msg.buttons[3] = Y
    # msg.buttons[4] = left trigger
    # msg.buttons[5] = right trigger
    # msg.buttons[6] = back button
    # msg.buttons[7] = start button
    # msg.buttons[8] = dunno, probably mode but it doesn't register
    # msg.buttons[9] = left stick press
    # msg.buttons[10] = right stick press

    forward = msg.axes[1]
    strafe = msg.axes[0]
    turn = msg.axes[3]

    lfl = (forward - strafe - turn) # Lateral Front Left
    lfr = (forward + strafe - turn) # Lateral Front Right
    lbl = (forward + strafe + turn) # Lateral Back Left
    lbr = (forward - strafe + turn) # Lateral Back Right

    lfl = clamp(lfl, -1.0, 1.0)
    lfr = clamp(lfr, -1.0, 1.0)
    lbl = clamp(lbl, -1.0, 1.0)
    lbr = clamp(lbr, -1.0, 1.0)

    global old_lfl
    global old_lfr
    global old_lbl
    global old_lbr

    command = ""

    if lfl != old_lfl:
        command += "lfl {} \n".format(to_pwm(lfl))
        old_lfl = lfl
    
    if lfr != old_lfr:
        command += "lfr {} \n".format(to_pwm(lfr))
        old_lfr = lfr

    if lbl != old_lbl:
        command += "lbl {} \n".format(to_pwm(lbl))
        old_lbl = lbl

    if lbr != old_lbr:
        command += "lbr {} \n".format(to_pwm(lbr))
        old_lbr = lbr

    rospy.loginfo("Publishing: {}".format(command))
    pub.publish(command)

rospy.init_node('joy_to_motor', anonymous=True)
pub = rospy.Publisher('motor_command', String, queue_size=10)
rospy.Subscriber('joy', Joy, joy_callback)
rospy.spin()
