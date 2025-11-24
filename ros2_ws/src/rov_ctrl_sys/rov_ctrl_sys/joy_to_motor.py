import rclpy
from rov_ctrl_sys.subscriber_publisher_general import SubscriberPublisher
from rclpy.signals import SignalHandlerOptions
import rclpy.qos as QoS

from sensor_msgs.msg import Joy

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
        super().__init__('joy_to_motor', Joy, 'joy', Joy, 'motor_command', sub_qos, pub_qos)

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
