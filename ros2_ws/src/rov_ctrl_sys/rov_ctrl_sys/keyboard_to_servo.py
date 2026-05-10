import rclpy
from rov_ctrl_sys.subscriber_publisher_general import SubscriberPublisher
from rclpy.signals import SignalHandlerOptions
import rclpy.qos as QoS
from rcl_interfaces.msg import ParameterDescriptor

from std_msgs.msg import String

def clamp(num, min_value, max_value):
    return max(min_value, min(max_value, num))

def to_pwm(cmd, start=1000, end=2000):
    range = end - start
    return int(((cmd + 1.0) / 2.0) * range + start)


class KeyboardToServo(SubscriberPublisher):

    def __init__(self):
        sub_qos = QoS.QoSProfile(
            depth=10, 
            reliability=QoS.ReliabilityPolicy.RELIABLE,
            durability=QoS.DurabilityPolicy.VOLATILE
        )
        pub_qos = QoS.QoSProfile(
            depth=10, 
            reliability=QoS.ReliabilityPolicy.RELIABLE,
            durability=QoS.DurabilityPolicy.VOLATILE
        )
        super().__init__('keyboard_to_servo', String, 'key_states', String, 'servo_command', sub_qos, pub_qos)
        self.old_values = {
                'camera_x': 0.0,
                'camera_y': 0.0,
                'dome_lights_max': 1.0,
                'ext_lights_max': 1.0
        }
        self.target = 'camera'
        self.commands = dict()
        self.vertical = {
                'camera': 'camera_y',
                'dome_lights': 'dome_lights_max',
                'ext_lights': 'ext_lights_max'
        }
        self.horizontal = {
                'camera': 'camera_x',
                'dome_lights': '',
                'ext_lights': ''
        }
        self.move_quantity = {
                'camera': 0.04,
                'dome_lights': 0.02,
                'ext_lights': 0.02,
        }

    def process_motor(self, key, value, start=1000, end=2000):
        value = clamp(value, -1.0, 1.0)
        if value != self.old_values[key]:
            pwm = to_pwm(value, start, end)
            self.commands[key] = pwm
            self.old_values[key] = value
        else:
            self.commands.pop(key, None)

    def process_command(self, key, value):
        if value != self.old_values[key]:
            self.commands[key] = value
            self.old_values[key] = value
        else:
            self.commands.pop(key, None)

    def generate_pub_msg(self, msg):
        keys = set(msg.data.split(','))

        if 'C' in keys:
            self.target = 'camera'
        elif 'D' in keys:
            self.target = 'dome_lights'
        elif 'E' in keys:
            self.target = 'ext_lights'

        if self.vertical[self.target] != '':
            if "UP" in keys:
                vertical = clamp(self.old_values[self.vertical[self.target]] + self.move_quantity[self.target],-1.0,1.0)
            elif "DOWN" in keys:
                vertical = clamp(self.old_values[self.vertical[self.target]] - self.move_quantity[self.target],-1.0,1.0)
            else:
                vertical = clamp(self.old_values[self.vertical[self.target]],-1.0,1.0)

        if self.horizontal[self.target] != '':
            if "RIGHT" in keys:
                horizontal = clamp(self.old_values[self.horizontal[self.target]] + self.move_quantity[self.target],-1.0,1.0)
            elif "LEFT" in keys:
                horizontal = clamp(self.old_values[self.horizontal[self.target]] - self.move_quantity[self.target],-1.0,1.0)
            else:
                horizontal = clamp(self.old_values[self.horizontal[self.target]],-1.0,1.0)

        if "BACKSPACE" in keys:
            if self.target == 'camera':
                if 'X' in keys:
                    horizontal = 0.0
                if 'Y' in keys:
                    vertical = 0.0
            else:
                vertical = 1.0

        if self.vertical[self.target] != '':
            if self.target == 'camera':
                self.process_motor(self.vertical['camera'], vertical, 1000, 2000)
            else:
                horizontal = clamp(vertical, 0.0, 1.0)
                self.process_command(self.vertical[self.target], vertical)

        if self.horizontal[self.target] != '':
            if self.target == 'camera':
                self.process_motor(self.horizontal['camera'], horizontal, 1000, 2000)
            else:
                horizontal = clamp(horizontal, 0.0, 1.0)
                self.process_command(self.horizontal[self.target], horizontal)


        if self.commands:
            new_msg = String()
            new_msg.data = ','.join(f'{k}={v:0.2f}' for k,v in self.commands.items())
            self.get_logger().debug(f"servo_commands: {new_msg.data}")
            self.commands.clear()
            return new_msg
        else:
            return None

def main(args=None):
    signal_handler_choice = SignalHandlerOptions(SignalHandlerOptions.SIGTERM)
    rclpy.init(args=args, signal_handler_options=signal_handler_choice)

    node = KeyboardToServo()

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
