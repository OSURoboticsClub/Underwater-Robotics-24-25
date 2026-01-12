import rclpy
from rclpy.node import Node

# This imports QoSProfiles, the instructions for handling messages within a topic
# There are 3 different parameters that we care about often:
#   depth: how many messages can be stored/queued at once
        # takes an integer number of messages
#   reliability: how does the publisher handle the potential for missed messages
        # 2 options:
        #   BEST_EFFORT: Send the message and try to deliver it, but if it fails
        #       don't resend or try again
        #   RELIABLE: When a message is sent, ensure all subscribers receive it, 
        #       resending as necessary
#   durability: how does the publisher handle new subscribers joining after 
#       changes have been made
        # 2 options:
        #   TRANSIENT_LOCAL: When a new node subscribes, transmit past messages 
        #       in order to get them up-to-date
        #   VOLATILE: When a new node subscribes, make no attempt to update them
from rclpy.qos import QoSProfile

# This class is a representation of a node that subscribes to one topic and 
# publishes to a different topic
class SubscriberPublisher(Node):

    # Constructor for this class
    # Params:
    #   name: a string representing the name for this node
    #   sub_topic_type: the type of message that is published to the topic this 
    #       node subscribes to
    #   sub_topic_name: the name of the topic this node subscribes to
    #   pub_topic_type: the type of message that is published to the topic this 
    #       node publishes to
    #   pub_topic_name: the name of the topic this node publishes to
    #   sub_qos_profile: an optional parameter providing a QoS profile
    #   pub_qos_profile: an optional parameter providing a QoS profile
    #
    #       Both QoS profiles default to BEST_EFFORT, RELIABLE, with a depth of 10
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
