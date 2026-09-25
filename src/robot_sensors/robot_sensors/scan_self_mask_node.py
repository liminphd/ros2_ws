import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from rclpy.qos import qos_profile_sensor_data


class ScanSelfMask(Node):
    def __init__(self):
        super().__init__('scan_self_mask')

        self.sub = self.create_subscription(
            LaserScan,
            '/scan_multi_raw',
            self.cb,
            qos_profile_sensor_data
        )

        self.pub = self.create_publisher(
            LaserScan,
            '/scan_multi',
            qos_profile_sensor_data
        )

        # 临时静态 self-mask，base_link 坐标
        # 只屏蔽已确认的右侧车体/机械臂自身区域
        self.x_min = -0.10
        self.x_max = 0.45
        self.y_min = -1.15
        self.y_max = -0.65

        self.get_logger().info(
            'Self mask active: '
            f'x=[{self.x_min},{self.x_max}], '
            f'y=[{self.y_min},{self.y_max}]'
        )

    def cb(self, msg):
        out = LaserScan()
        out.header = msg.header
        out.angle_min = msg.angle_min
        out.angle_max = msg.angle_max
        out.angle_increment = msg.angle_increment
        out.time_increment = msg.time_increment
        out.scan_time = msg.scan_time
        out.range_min = msg.range_min
        out.range_max = msg.range_max
        out.intensities = list(msg.intensities)

        ranges = list(msg.ranges)

        for i, r in enumerate(ranges):
            if not math.isfinite(r):
                continue

            a = msg.angle_min + i * msg.angle_increment
            x = r * math.cos(a)
            y = r * math.sin(a)

            if (
                self.x_min <= x <= self.x_max
                and self.y_min <= y <= self.y_max
            ):
                ranges[i] = float('inf')

        out.ranges = ranges
        self.pub.publish(out)


def main():
    rclpy.init()
    node = ScanSelfMask()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
