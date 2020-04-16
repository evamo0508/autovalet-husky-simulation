#!/usr/bin/env python
# license removed for brevity
import rospy
from gazebo_msgs.msg import LinkStates
from nav_msgs.msg import Odometry
from tf.transformations import euler_from_quaternion

import numpy as np

class Localization_validation:
    def __init__(self, gt_topic, est_topic, sample_dist):
        self.gt_handle = rospy.Subscriber(gt_topic, LinkStates, self.gt_cb)
        self.est_handle = rospy.Subscriber(est_topic, Odometry, self.est_cb)
        self.sample_dist = sample_dist

        self.gt = None
        self.estimate = None
        self.last_gt = None

        """
        To ping the first message of gt and populate the world to pose offset
        """
        self.isFirstCb = True
        self.offset = None

    def gt_cb(self, gt):
        """
        localization validation callback function
        gt: ground truth published by gazebo link state /::base_link w.r.t the gazebo world origin
        """

        #TODO: get list index from name of first message
        self.gt = gt.pose[-5]
        if(self.isFirstCb is True):
            self.last_gt = np.array([self.gt.position.x, self.gt.position.y, self.quat_to_euler(self.gt.orientation)[2]])
            self.offset = np.array([self.gt.position.x,  self.gt.position.y, self.quat_to_euler(self.gt.orientation)[2]])
            self.isFirstCb = False

    def est_cb(self, est):
        """
        pose: estimated pose published by est_topic (in our case: EKF localization's filtered odometry)
        updates the localization error variables
        Error values are updated here as the EKF odom is of lower publish rate as compared to Gazebo state publisher
        """
        self.estimate = est.pose.pose

        if(self.last_gt is not None and self.gt is not None):
            cur_pose = np.array([self.estimate.position.x, self.estimate.position.y, self.quat_to_euler(self.estimate.orientation)[2]])
            gt_pose = np.array([self.gt.position.x, self.gt.position.y, self.quat_to_euler(self.gt.orientation)[2]])
            
            dist_moved = np.linalg.norm(gt_pose[:-1] - self.last_gt[:-1])
            if(dist_moved > self.sample_dist):
                current_error_position = np.linalg.norm(cur_pose[:-1] - (gt_pose[:-1] - self.offset[:-1]))
                current_error_heading = np.linalg.norm(cur_pose[-1] - (gt_pose[-1] - self.offset[-1]))
                print("Individual Errors: ", cur_pose - (gt_pose - self.offset))
                print("Current Euclidean error: ", current_error_position, current_error_heading)
                self.last_gt = gt_pose

    def quat_to_euler(self, q):
        # euler indexing as RPY
        quaternion = (q.x, q.y, q.z, q.w)
        euler = euler_from_quaternion(quaternion)
        return euler


def main():

    print("Starting Localization Error calculator node")
    rospy.init_node("localization_validation", anonymous=False)
    
    ground_truth_topic = '/gazebo/link_states'
    estimate_topic = '/odometry/filtered'
    sample_dist = 0.3

    Localization_validation(ground_truth_topic, estimate_topic, sample_dist)

    while not rospy.is_shutdown():
        pass

if __name__ == '__main__':
    main()