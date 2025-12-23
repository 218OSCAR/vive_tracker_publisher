#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
import pysurvive
import sys
import time
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped


class ViveTrackerPublisher(Node):
    def __init__(self):
        super().__init__('vive_tracker_publisher')

        # create Publisher
        self.pose_pub = self.create_publisher(PoseStamped, '/vive_tracker/pose', 10)
        self.get_logger().info("Initializing libsurvive context...")

        # Initialize libsurvive
        self.actx = pysurvive.SimpleContext(sys.argv)
        self.trackers = [obj for obj in self.actx.Objects()]
        for obj in self.trackers:
            self.get_logger().info(f"Found device: {obj.Name().decode('utf-8')}")

        # Timer (optional, if you want periodic checking)
        self.timer = self.create_timer(0.01, self.timer_callback)  # 100 Hz
        # Creating a Broadcaster
        self.br = TransformBroadcaster(self)

    def timer_callback(self):
        if self.actx.Running():
            updated = self.actx.NextUpdated()
            if updated:
                pose_obj = updated.Pose()
                pose = pose_obj[0]
                timestamp = pose_obj[1]

                # Creating a ROS PoseStamped Message
                msg = PoseStamped()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.header.frame_id = "world"

                msg.pose.position.x = pose.Pos[0]
                msg.pose.position.y = pose.Pos[1]
                msg.pose.position.z = pose.Pos[2]

                msg.pose.orientation.w = pose.Rot[0]
                msg.pose.orientation.x = pose.Rot[1]
                msg.pose.orientation.y = pose.Rot[2]
                msg.pose.orientation.z = pose.Rot[3]

                self.pose_pub.publish(msg)
                self.get_logger().debug(f"Published pose for {updated.Name().decode('utf-8')}")


                t = TransformStamped()
                t.header.stamp = self.get_clock().now().to_msg()
                t.header.frame_id = "world"
                t.child_frame_id = "vive_tracker"

                t.transform.translation.x = pose.Pos[0]
                t.transform.translation.y = pose.Pos[1]
                t.transform.translation.z = pose.Pos[2]

                t.transform.rotation.w = pose.Rot[0]
                t.transform.rotation.x = pose.Rot[1]
                t.transform.rotation.y = pose.Rot[2]
                t.transform.rotation.z = pose.Rot[3]
                # Publish a TransformStamped per frame
                self.br.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    node = ViveTrackerPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down Vive Tracker publisher...')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
