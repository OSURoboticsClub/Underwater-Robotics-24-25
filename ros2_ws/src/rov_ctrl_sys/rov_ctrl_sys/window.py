import rclpy
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from rov_ctrl_sys.subscriber_general import Subscriber
from rov_ctrl_sys.text_print import TextPrint
from sensor_msgs.msg import Image
from std_msgs.msg import String

import pygame
import threading
import json
import pathlib

class Window(Node):

    def __init__(self):
        super().__init__('window')

        self.declare_parameter('fullscreen', True)
        self.fullscreen = self.get_parameter('fullscreen').value
        self.declare_parameter('image_width', 640)
        self.image_width = self.get_parameter('image_width').value
        self.declare_parameter('image_height', 480)
        self.image_height = self.get_parameter('image_height').value

        pygame.init()
        self.running = True
#         self.screen = pygame.display.set_mode((1080,720), flags=pygame.SCALED)
        self.screen = pygame.display.set_mode((640,360), flags=pygame.SCALED)
        if self.fullscreen:
            pygame.display.toggle_fullscreen()

        pygame.display.set_caption("ROV Control Window")
        pygame.mouse.set_visible(True)
        self.text = TextPrint()
        self.reset_screen()

#        self.clock = pygame.time.Clock()
        self.debug = False
        self.img_size = (self.image_width, self.image_height)
        self.buffer_size = self.img_size[0] * self.img_size[1] * 3
        self.buffers = [bytearray(self.buffer_size),bytearray(self.buffer_size)]
        self.img_surfaces = [pygame.image.frombuffer(self.buffers[0], self.img_size, 'RGB'), pygame.image.frombuffer(self.buffers[1], self.img_size, 'RGB')]
        self.front_idx = 0
        self.new_frame = False
        self.img_lock = threading.Lock()
        self.img_dir = str(pathlib.Path.home()) + '/Underwater-Robotics-24-25/crab_detect/rov_photos/'
        self.img_num = 1

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
                pygame.K_p: 'P', # crab processing
                pygame.K_f: 'F', # fullscreen
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

        self.f_pressed = False


        self.pub = self.create_publisher(String, 'key_states', 10)
        timer_delay = 1.0/30.0 # seconds
        self.timer = self.create_timer(timer_delay, self.timer_callback)
        self.sub_img = self.create_subscription(Image,
                'image_raw',
                self.image_callback,
                1)
        self.sub_img, self.pub, self.sub_img # prevent unused variable warnings
    
    def reset_screen(self):
        self.screen.fill(pygame.Color(255, 255, 255))
        self.text.indent().set_color((255,0,0))
#         self.text.tprintln(self.screen, "Press both ESC and delete to exit")
        self.text.set_color((0,0,0)).reset()
        pygame.display.flip()

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
        capture_frame = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.get_logger().info("Window closed, shutting down")
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LSHIFT:
                    self.debug = not self.debug
                    continue
                elif event.key == pygame.K_RETURN:
                    capture_frame = True
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
            if capture_frame:
                filename = self.img_dir + 'crab' + str(self.img_num) + '.jpeg'
                pygame.image.save(self.img_surfaces[self.front_idx], filename)
                self.img_num += 1
                self.get_logger().info(f'Saving image to: {filename}')

        if new_frame:
            scaled = pygame.transform.scale(img_surface, (480, 360))
            updated_rects.append(self.screen.blit(scaled, ( 80,000)))
#             updated_rects.append(self.screen.blit(img_surface, (100,100)))

        if not self.f_pressed and 'F' in self.held_keys:
            self.fullscreen = not self.fullscreen
            if not self.fullscreen:
                self.screen = pygame.display.set_mode((640,360), flags=pygame.SCALED)
            else:
                pygame.display.toggle_fullscreen()
            self.reset_screen()
            self.f_pressed = True
        elif self.f_pressed and 'F' not in self.held_keys:
            self.f_pressed = False

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
