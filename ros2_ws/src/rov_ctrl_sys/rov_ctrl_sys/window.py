import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from rov_ctrl_sys.subscriber_general import Subscriber
from sensor_msgs.msg import Image
from std_msgs.msg import String

import pygame

class TextPrint:
    def __init__(self):
        self.reset()
        self._font = pygame.font.SysFont('DejaVu Sans Mono', 20)

    def tprintln(self, screen, text):
        self.tprint(screen, text)
        self._y += self._line_height
        self._x_offset = 0

    def tprint(self, screen, text):
        text_bitmap = self._font.render(text, True, self.color)
        screen.blit(text_bitmap, (self._x + self._x_offset, self._y))
        self._x_offset += text_bitmap.get_width()

    def reset(self):
        self._x = 10
        self._y = 10
        self._line_height = 22
        self._x_offset = 0
        self.color = (0,0,0)

    def indent(self):
        self._x += 10
    
    def unindent(self):
        self._x -= 10
    
    def get_x(self):
        return self._x
    
    def get_y(self):
        return self._y

    def set_x(self, new_x):
        self._x = new_x

    def set_y(self, new_y):
        self._y = new_y

    def set_color(self, new_color):
        self.color = new_color

class Window(Node):

    def __init__(self):
        super().__init__('window')
        self.sub_img = self.create_subscription(Image,
                'image_raw',
                self.image_callback,
                100)
        self.sub_img # prevent unused variable warning

        self.pub = self.create_publisher(String, 'key_states', 10)
        timer_delay = 1/30 # seconds
        self.timer = self.create_timer(timer_delay, self.timer_callback)

        pygame.init()
        self.running = True
        self.screen = pygame.display.set_mode((1080,720))
#        self.clock = pygame.time.Clock()
        self.debug = False

    def image_callback(self, msg):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.get_logger().info("Window closed, shutting down")
                return
        self.screen.fill("purple")

        if msg.encoding == 'rgb8':
            byte_array = bytearray(msg.data)
            img = pygame.image.frombuffer(byte_array, (msg.width, msg.height), 'RGB')

            self.screen.blit(pygame.transform.scale(img, (640,480)), (100,100))
            pygame.display.flip()

    def timer_callback(self):


    def destroy_node(self):
        pygame.quit()
        super().destroy_node()


def main(args=None):
    signal_handler_choice = SignalHandlerOptions(SignalHandlerOptions.SIGTERM)
    rclpy.init(args=args, signal_handler_options=signal_handler_choice)

    node = TestWindow()

    try:
        while rclpy.ok() and node.running:
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
