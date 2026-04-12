import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from rov_ctrl_sys.subscriber_general import Subscriber
from sensor_msgs.msg import Image
from std_msgs.msg import String

import pygame
import threading
import json

class TextPrint:
    def __init__(self):
        self.reset()
        self._font = pygame.font.SysFont('DejaVu Sans Mono', 20)

    def tprintln(self, screen, text):
        self.tprint(screen, text)
        self._y += self._line_height
        self._x_offset = 0
        return self

    def tprint(self, screen, text):
        text_bitmap = self._font.render(text, True, self.color)
        screen.blit(text_bitmap, (self._x + self._x_offset, self._y))
        self._x_offset += text_bitmap.get_width()
        return self

    def reset(self):
        self._x = 10
        self._y = 10
        self._line_height = 22
        self._x_offset = 0
        self.color = (0,0,0)
        return self

    def indent(self):
        self._x += 10
        return self
    
    def unindent(self):
        self._x -= 10
        return self
    
    def get_x(self):
        return self._x
    
    def get_y(self):
        return self._y

    def set_x(self, new_x):
        self._x = new_x
        return self

    def set_y(self, new_y):
        self._y = new_y
        return self

    def set_color(self, new_color):
        self.color = new_color
        return self

class Window(Node):

    def __init__(self):
        super().__init__('window')

        pygame.init()
        self.running = True
        self.screen = pygame.display.set_mode((1080,720))
        pygame.display.set_caption("ROV Control Window")
        pygame.mouse.set_visible(True)
        self.text = TextPrint()
        self.screen.fill(pygame.Color(255, 255, 255))
        self.text.indent().set_color((255,0,0))
        self.text.tprintln(self.screen, "Press both ESC and delete to exit")
        self.text.set_color((0,0,0)).reset()
        pygame.display.flip()

#        self.clock = pygame.time.Clock()
        self.debug = False
        self.img_size = (640,480) # will be ros parameterized later
        self.buffer_size = self.img_size[0] * self.img_size[1] * 3
        self.buffers = [bytearray(self.buffer_size),bytearray(self.buffer_size)]
        self.img_surfaces = [pygame.image.frombuffer(self.buffers[0], self.img_size, 'RGB'), pygame.image.frombuffer(self.buffers[1], self.img_size, 'RGB')]
        self.front_idx = 0
        self.new_frame = False
        self.img_lock = threading.Lock()

        self.held_keys = set()
        self.keymap = {
                pygame.K_UP: 'UP',          # change controls
                pygame.K_DOWN: 'DOWN',      # ^^
                pygame.K_LEFT: 'LEFT',      # ^^
                pygame.K_RIGHT: 'RIGHT',    # ^^
                pygame.K_BACKSPACE: "BACKSPACE", # reset
                pygame.K_c: 'C', # camera
                pygame.K_d: 'D', # dome lights
                pygame.K_e: 'E', # external lights
                pygame.K_x: 'X',
                pygame.K_y: 'Y',
#                 pygame.K_w: 'W',
#                 pygame.K_a: 'A',
#                 pygame.K_s: 'S',
#                 pygame.K_d: 'D',
#                 pygame.K_SPACE: 'SPACE',
#                 pygame.K_RETURN: 'ENTER',
#                 pygame.K_1: '1',
#                 pygame.K_2: '2',
#                 pygame.K_3: '3',
#                 pygame.K_4: '4',
                pygame.K_ESCAPE: "ESC", # used to close window
                pygame.K_DELETE: "DEL"  # ^^
                }
        self.last_msg = None


        self.pub = self.create_publisher(String, 'key_states', 10)
        timer_delay = 1.0/30.0 # seconds
        self.timer = self.create_timer(timer_delay, self.timer_callback)
        self.sub_img = self.create_subscription(Image,
                'image_raw',
                self.image_callback,
                1)
        self.sub_img, self.pub, self.sub_img # prevent unused variable warnings

    def image_callback(self, msg):
        if (msg.encoding == "rgb8") and (self.img_size == (msg.width,msg.height)) and (len(msg.data) == msg.step * msg.height):
            with self.img_lock:
                back_idx = self.front_idx ^ 1

            row_out = msg.width * 3
            if row_out > msg.step:
                return

            if msg.step == row_out:
                self.buffers[back_idx][:msg.height * row_out] = msg.data
            else:
                for y in range(msg.height):
                    self.buffers[back_idx][y*row_out:(y+1)*row_out] = msg.data[y*msg.step:y*msg.step + row_out]

            with self.img_lock:
                self.front_idx = back_idx
                self.new_frame = True

    def timer_callback(self):
        key_changed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.get_logger().info("Window closed, shutting down")
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LSHIFT:
                    self.debug = not self.debug
                    continue

                name = self.keymap.get(event.key)
                if (name is not None) and (name not in self.held_keys):
                        self.held_keys.add(name)
                        key_changed = True
            elif event.type == pygame.KEYUP:
                name = self.keymap.get(event.key)
                if name is not None and name in self.held_keys:
                    self.held_keys.remove(name)
                    key_changed = True
            pass

        if "ESC" in self.held_keys and "DEL" in self.held_keys:
            self.running = False
            return

        if key_changed:
            msg = String()
            msg.data = ",".join(self.held_keys) # join(sorted(self.held_keys))
            self.pub.publish(msg)
            self.last_msg = msg
        elif self.last_msg:
            self.pub.publish(self.last_msg)

        updated_rects = []

        with self.img_lock:
            new_frame = self.new_frame
            if new_frame:
                img_surface = self.img_surfaces[self.front_idx]
                self.new_frame = False

        if new_frame:
            updated_rects.append(self.screen.blit(img_surface, (100,100)))

        pygame.display.update(updated_rects)

    def destroy_node(self):
        pygame.quit()
        super().destroy_node()


def main(args=None):
    signal_handler_choice = SignalHandlerOptions(SignalHandlerOptions.SIGTERM)
    rclpy.init(args=args, signal_handler_options=signal_handler_choice)

    node = Window()

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
