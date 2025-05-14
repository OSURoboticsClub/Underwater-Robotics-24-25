#!/usr/bin/env python
import rospy
from std_msgs.msg import String
import pygame
import json

def main():
    rospy.init_node('pygame_key_publisher')
    pub = rospy.Publisher('key_states', String, queue_size=10)

    pygame.init()
    screen = pygame.display.set_mode((0,0),pygame.FULLSCREEN)
    pygame.display.set_caption("Keyboard Listener")
    pygame.mouse.set_visible(True)

    clock = pygame.time.Clock()
    held_keys = set()

    keymap = {
        pygame.K_UP: 'UP',
        pygame.K_DOWN: 'DOWN',
        pygame.K_LEFT: 'LEFT',
        pygame.K_RIGHT: 'RIGHT',
        pygame.K_LEFTBRACKET: "[",
        pygame.K_RIGHTBRACKET: "]",
        pygame.K_w: 'W',
        pygame.K_a: 'A',
        pygame.K_s: 'S',
        pygame.K_d: 'D',
        pygame.K_SPACE: 'SPACE',
        pygame.K_RETURN: 'ENTER',
        pygame.K_ESCAPE: 'ESCAPE'
    }

    running = True
    while (not rospy.is_shutdown()) and running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                rospy.signal_shutdown('Window closed')
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key in keymap:
                    held_keys.add(keymap[event.key])
            elif event.type == pygame.KEYUP:
                if event.key in keymap and keymap[event.key] in held_keys:
                    held_keys.remove(keymap[event.key])

        # Publish as JSON string
        pub.publish(json.dumps(sorted(list(held_keys))))

        clock.tick(30)  # Limit to 30 FPS

    pygame.quit()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
