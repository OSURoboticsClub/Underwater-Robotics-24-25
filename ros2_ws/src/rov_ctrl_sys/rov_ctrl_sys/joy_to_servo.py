import rclpy
from rov_ctrl_sys.subscriber_publisher_general import SubscriberPublisher
from rclpy.signals import SignalHandlerOptions
import rclpy.qos as QoS
from rcl_interfaces.msg import ParameterDescriptor

from sensor_msgs.msg import Joy
from std_msgs.msg import String

def clamp(num, min_value, max_value):
    return max(min_value, min(max_value, num))

def to_pwm(cmd, start=1000, end=2000):
    range = end - start
    return int(((cmd + 1.0) / 2.0) * range + start)


class JoyToServo(SubscriberPublisher):

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
        super().__init__('joy_to_servo', Joy, 'joy', String, 'servo_command', sub_qos, pub_qos)
        self.old_values = {
                'manip': 0.0,
                'manip_rotate': 0.0,
                'dome_lights': 0.0,
                'ext_lights': 0.0
        }
        self.y_pressed = False
        self.a_pressed = False
        self.b_pressed = False
        self.commands = dict()

    def process_motor(self, key, value, send_to_pwm = True):
        value = clamp(value, -1.0, 1.0)
        if value != self.old_values[key]:
            if send_to_pwm:
                pwm = to_pwm(value)
            else:
                pwm = value

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
        manip = self.old_values['manip']
        dome_lights = self.old_values['dome_lights']
        ext_lights = self.old_values['ext_lights']
        if not self.a_pressed and msg.buttons[0] == 1:
            self.a_pressed = True
            if self.old_values['ext_lights'] == 1.0:
                ext_lights = 0.0
            else:
                ext_lights = 1.0
        elif self.a_pressed and msg.buttons[0] == 0:
            self.a_pressed = False

        if not self.y_pressed and msg.buttons[3] == 1:
            self.y_pressed = True
            if self.old_values['dome_lights'] == 1.0:
                dome_lights = 0.0
            else:
                dome_lights = 1.0
        elif self.y_pressed and msg.buttons[3] == 0:
            self.y_pressed = False

        if not self.b_pressed and msg.buttons[1] == 1:
            self.b_pressed = True
            if self.old_values['manip'] == 1.0:
                manip = 0.0
            else:
                manip = 1.0
        elif self.b_pressed and msg.buttons[1] == 0:
            self.b_pressed = False

        if msg.buttons[4] == 1:
            manip_rotate = 1.0
        elif msg.buttons[5] == 1:
            manip_rotate = -1.0
        else:
            manip_rotate = 0.0

        self.process_motor('manip', manip, False)
        self.process_motor('manip_rotate', manip_rotate)
        self.process_motor('dome_lights', dome_lights, False)
        self.process_motor('ext_lights', ext_lights, False)

        if self.commands:
            new_msg = String()
            new_msg.data = ','.join(f'{k}={v}' for k,v in self.commands.items())
            self.get_logger().debug(f"servo_commands: {new_msg.data}")
            return new_msg
        else:
            return None

def main(args=None):
    signal_handler_choice = SignalHandlerOptions(SignalHandlerOptions.SIGTERM)
    rclpy.init(args=args, signal_handler_options=signal_handler_choice)

    node = JoyToServo()

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=1)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down (SIGINT)")
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
