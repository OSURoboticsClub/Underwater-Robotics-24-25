import rclpy
from rclpy.qos import QoSProfile
from rclpy.node import Node

class SubscriberPublisher(Node):

    def __init__(self, name, 
            sub_topic_type, sub_topic_name,
            pub_topic_type, pub_topic_name,
            sub_qos_profile=10, pub_qos_profile=10):
        super().__init__(name)
        if isinstance(sub_qos_profile, int):
            sub_qos_profile = QoSProfile(depth=sub_qos_profile)
        if isinstance(pub_qos_profile, int):
            pub_qos_profile = QoSProfile(depth=pub_qos_profile)
        self.publisher_ = self.create_publisher(pub_topic_type, pub_topic_name, pub_qos_profile)
        self.subscription = self.create_subscription(
                sub_topic_type,
                sub_topic_name,
                self.listener_callback,
                sub_qos_profile)
        self.subscription # prevent unused variable warning

    def listener_callback(self, msg):
        pub_msg = self.generate_pub_msg(msg)
        if pub_msg is not None:
            self.publisher_.publish(pub_msg)

    def generate_pub_msg(self, msg):
        self.get_logger().warn(f"Using default publish, publishing input unchanged: \"{msg}\"")
        return msg
