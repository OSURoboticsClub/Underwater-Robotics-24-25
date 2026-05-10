import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

class Subscriber(Node):

    def __init__(self, name, topic_type, topic_name, qos_profile=10):
        super().__init__(name)
        if isinstance(qos_profile, int):
            qos_profile = QoSProfile(depth=qos_profile)
        self.subscription = self.create_subscription(topic_type, 
                topic_name, 
                self.listener_callback,
                qos_profile
        )
        self.subscription # prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().warn(f'Using default callback. Received: {msg}')
