import rclpy
from rov_ctrl_sys.subscriber_publisher_general import SubscriberPublisher
from rclpy.signals import SignalHandlerOptions
import rclpy.qos as QoS

from sensor_msgs.msg import Joy
from std_msgs.msg import String
import json

def clamp(num, min_value, max_value):
    return max(min_value, min(max_value, num))

def to_pwm(cmd, start=1000, end=2000):
    range = end - start
    return int(((cmd + 1.0) / 2.0) * range + start)


class JoyToMotor(SubscriberPublisher):

    def __init__(self):
        sub_qos = QoS.QoSProfile(
                depth=10, 
                reliability=QoS.ReliabilityPolicy.BEST_EFFORT,
                durability=QoS.DurabilityPolicy.VOLATILE
                )
        pub_qos = QoS.QoSProfile(
                depth=10, 
                reliability=QoS.ReliabilityPolicy.RELIABLE,
                durability=QoS.DurabilityPolicy.VOLATILE
                )
        super().__init__('joy_to_motor', Joy, 'joy', String, 'motor_command', sub_qos, pub_qos)
        self.ltrigger_been_pressed = False
        self.rtrigger_been_pressed = False
        self.old_values = {
                'lfl': 0.0,
                'lfr': 0.0,
                'lbl': 0.0,
                'lbr': 0.0,
                'vfl': 0.0,
                'vfr': 0.0,
                'vbl': 0.0,
                'vbr': 0.0
                }
        self.commands = dict()

    def process_motor(self, key, value):
        value = clamp(value, -1.0, 1.0)
        if value != self.old_values[key]:
            pwm = to_pwm(value)
            self.commands[key] = pwm
            self.old_values[key] = value
        else:
            self.commands.pop(key, None)

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
    # msg.buttons[4] = left shoulder
    # msg.buttons[5] = right shoulder
    # msg.buttons[6] = back button
    # msg.buttons[7] = start button
    # msg.buttons[8] = dunno, probably mode but it doesn't register
    # msg.buttons[9] = left stick press
    # msg.buttons[10] = right stick press
    def generate_pub_msg(self, msg):
        if ((not self.rtrigger_been_pressed) and msg.axes[5] != 0.0): 
            self.rtrigger_been_pressed = True

        if ((not self.ltrigger_been_pressed) and msg.axes[2] != 0.0): 
            self.ltrigger_been_pressed = True

        forward = msg.axes[1]
        strafe = msg.axes[0]
        turn = msg.axes[3]
        roll = msg.axes[6]
        pitch = msg.axes[7]
        if not self.ltrigger_been_pressed and not self.rtrigger_been_pressed:
            lift = 0.0
        elif not self.ltrigger_been_pressed and self.rtrigger_been_pressed:
            lift = -1 * ((msg.axes[5] - 1.0) / 2.0)
        elif self.ltrigger_been_pressed and not self.rtrigger_been_pressed:
            lift = (msg.axes[2] - 1.0) / 2.0
        else:
            lift = ((msg.axes[2] - 1.0) / 2.0) - ((msg.axes[5] - 1.0) / 2.0)
        lift = clamp(lift, -1.0, 1.0)

        lateral_mod = 1.0 #rospy.get_param('~lateral', 1)
        vertical_mod = 1.0 #rospy.get_param('~vertical', 1)
        pitch_roll_mod = 1.0 #rospy.get_param('~pitch_roll', 1)

        lfl = (forward - strafe - turn) * lateral_mod # Lateral Front Left
        lfr = (forward + strafe - turn) * lateral_mod # Lateral Front Right
        lbl = (forward + strafe + turn) * lateral_mod # Lateral Back Left
        lbr = (forward - strafe + turn) * lateral_mod # Lateral Back Right
    
        vfl = vertical_mod * lift + ( roll - pitch) * pitch_roll_mod # Vertical Front Left
        vfr = vertical_mod * lift + ( roll + pitch) * pitch_roll_mod # Vertical Front Right
        vbl = vertical_mod * lift + (-roll - pitch) * pitch_roll_mod # Vertical Back Left
        vbr = vertical_mod * lift + (-roll + pitch) * pitch_roll_mod # Vertical Back Right

        self.process_motor('lfl', lfl)
        self.process_motor('lfr', lfr)
        self.process_motor('lbl', lbl)
        self.process_motor('lbr', lbr)
        self.process_motor('vfl', vfl)
        self.process_motor('vfr', vfr)
        self.process_motor('vbl', vbl)
        self.process_motor('vbr', vbr)

        if self.commands:
            new_msg = String()
            new_msg.data = json.dumps(self.commands)
            return new_msg
        else:
            return None

def main(args=None):
    signal_handler_choice = SignalHandlerOptions(SignalHandlerOptions.SIGTERM)
    rclpy.init(args=args, signal_handler_options=signal_handler_choice)

    node = JoyToMotor()

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=1)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down (Keyboard Interrupt)")
        pass
    finally:
        # Destroy the node explicitly
        # (optional - otherwise it will be done automatically
        # when the garbage collector destroys the node object)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
