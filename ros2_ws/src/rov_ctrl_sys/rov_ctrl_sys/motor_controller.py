import rclpy
from std_msgs.msg import String
from rov_ctrl_sys.subscriber_general import Subscriber
from rclpy.signals import SignalHandlerOptions
import rclpy.qos as QoS
from rcl_interfaces.msg import ParameterDescriptor

import serial
import json

class MotorController(Subscriber):

    def __init__(self):
        qos = QoS.QoSProfile(
            depth=10,
            reliability=QoS.ReliabilityPolicy.RELIABLE,
            durability=QoS.DurabilityPolicy.VOLATILE
        )

        super().__init__('motor_controller', String, 'motor_command', qos)
        port_descriptor = ParameterDescriptor(description='Serial port the motors are connected to')
        baud_descriptor = ParameterDescriptor(description='The rate used to communicate on the serial port')

        self.declare_parameter('port', '/dev/ttyUSB0', port_descriptor)
        self.declare_parameter('baud', 115200, port_descriptor)

        self.port = self.get_parameter('port').get_parameter_value().string_value
        self.baud = self.get_parameter('baud').get_parameter_value().integer_value

        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            self.ser.flushInput()
            self.ser.flushOutput()
            self.get_logger().info(f'Opened serial port{port} at {baud} baud.')
        except serial.SerialException as e:
            self.get_logger().error('Failed to open serial port {port}: {e}')
            self.ser = None

    def close_serial(self):
        self.get_logger().info('Shutting down motor_controller')
        if self.ser and self.ser.is_open:
            self.get_logger().info('Closing serial port')
            self.ser.close()
    
    def listener_callback(self, msg):
        if msg.data == "":
            self.get_logger().warn('Ignoring empty command')
        elif (not self.ser) or (not self.ser.is_open):
            self.get_logger().warn(f'Serial port is closed, rejecting command: {msg.data}')
        else:
            self.get_logger().debug(f'Sending to ESP32 {msg.data}')
            self.ser.write((msg.data + '\n').encode())


def main(args=None):
    signal_handler_choice = SignalHandlerOptions(SignalHandlerOptions.SIGTERM)
    rclpy.init(args=args, signal_handler_options=signal_handler_choice)

    node = MotorController()

    def shutdown_hook():
        node.close_serial()

    rclpy.get_default_context().on_shutdown(shutdown_hook)

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=1)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down (SIGINT)")
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
