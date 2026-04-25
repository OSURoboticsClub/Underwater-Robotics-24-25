# Underwater-Robotics-24-25
Code for the Underwater Robotics subteam of DAM Robotics at Oregon State University

To run the code, use "ros2 launch rov_ctrl_sys launch_ground.launch.py" on the ground station and "ros2 launch rov_ctrl_sys launch_rov.launch.py".

To upload code to the esps over ssh, use a variation on the following commands:
arduino-cli compile --fqbn esp32:esp32:esp32da ~/Underwater-Robotics-24-25/esp-32-code/servos-sensors/servos-sensors.ino
arduino-cli upload -p /dev/usb_right --fqbn esp32:esp32:esp32da ~/Underwater-Robotics-24-25/esp-32-code/servos-sensors/servos-sensors.ino

These commands (or variations) can be used to help setup automatic detection and naming of specific usb devices
udevadm info --attribute-walk --name=/dev/video2 > video2.txt
sudo udevadm control --reload-rules
sudo udevadm trigger
