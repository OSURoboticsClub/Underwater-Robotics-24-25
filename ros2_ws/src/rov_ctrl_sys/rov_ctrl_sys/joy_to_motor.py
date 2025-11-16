import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions

from sensor_msgs.msg import Joy

import json

class MinimalSubscriber(Node):

    def __init__(self):
        super().__init__('joy_to_motor')
        self.publisher_ = self.create_publisher(Joy, 'motor_command', 10)
        self.subscription = self.create_subscription(
                Joy,
                'joy',
                self.listener_callback,
                10)
        self.subscription # prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().info(f"I heard: \"{msg}\"")
        self.publisher_.publish(msg)


def main(args=None):
    signal_handler_choice = SignalHandlerOptions(SignalHandlerOptions.SIGTERM)
    rclpy.init(args=args, signal_handler_options=signal_handler_choice)

    minimal_subscriber = MinimalSubscriber()

    try:
        rclpy.spin(minimal_subscriber)
    except KeyboardInterrupt:
        minimal_subscriber.get_logger().info("Shutting down (Keyboard Interrupt)")
        pass
    finally:
        # Destroy the node explicitly
        # (optional - otherwise it will be done automatically
        # when the garbage collector destroys the node object)
        minimal_subscriber.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
