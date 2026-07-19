#include "node_lidar_ros.h"
#include "node_lidar.h"

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/laser_scan.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <std_msgs/msg/string.hpp>
#include <std_msgs/msg/u_int16.hpp>

#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl_conversions/pcl_conversions.h>

#include <chrono>
#include <cmath>
#include <cstddef>
#include <functional>
#include <memory>
#include <string>
#include <thread>


class LidarCommandSubscriber : public rclcpp::Node
{
public:
  LidarCommandSubscriber()
  : Node("cspc_lidar_command_subscriber")
  {
    subscription_ =
      this->create_subscription<std_msgs::msg::UInt16>(
        "lidar_status",
        10,
        std::bind(
          &LidarCommandSubscriber::topic_callback,
          this,
          std::placeholders::_1));
  }

private:
  void topic_callback(
    const std_msgs::msg::UInt16::SharedPtr msg)
  {
    switch (msg->data)
    {
      case 1:
        node_lidar.lidar_status.lidar_ready = true;
        node_lidar.lidar_status.lidar_abnormal_state = 0;
        RCLCPP_INFO(this->get_logger(), "Start lidar");
        break;

      case 2:
        node_lidar.lidar_status.lidar_ready = false;
        node_lidar.lidar_status.close_lidar = true;
        node_lidar.serial_port->write_data(end_lidar, 4);
        RCLCPP_INFO(this->get_logger(), "Stop lidar");
        break;

      case 3:
        node_lidar.serial_port->write_data(high_exposure, 4);
        RCLCPP_INFO(this->get_logger(), "High exposure");
        break;

      case 4:
        node_lidar.serial_port->write_data(low_exposure, 4);
        RCLCPP_INFO(this->get_logger(), "Low exposure");
        break;

      case 5:
        node_lidar.lidar_status.lidar_abnormal_state = 0;
        RCLCPP_INFO(this->get_logger(), "Clear abnormal state");
        break;

      case 6:
        node_lidar.serial_port->write_data(high_speed, 4);
        node_lidar.lidar_general_info.frequency_max = 103;
        node_lidar.lidar_general_info.frequency_min = 97;
        RCLCPP_INFO(this->get_logger(), "High speed");
        break;

      case 7:
        node_lidar.serial_port->write_data(low_speed, 4);
        node_lidar.lidar_general_info.frequency_max = 68;
        node_lidar.lidar_general_info.frequency_min = 52;
        RCLCPP_INFO(this->get_logger(), "Low speed");
        break;

      default:
        RCLCPP_WARN(
          this->get_logger(),
          "Unknown lidar command: %u",
          msg->data);
        break;
    }
  }

  rclcpp::Subscription<std_msgs::msg::UInt16>::SharedPtr
    subscription_;
};


void scan_to_point_cloud(
  const LaserScan & scan,
  sensor_msgs::msg::PointCloud2 & output,
  const std::string & frame_id)
{
  constexpr double degrees_to_radians =
    3.14159265358979323846 / 180.0;

  pcl::PointCloud<pcl::PointXYZ> cloud;

  cloud.header.frame_id = frame_id;
  cloud.width = static_cast<std::uint32_t>(
    scan.points.size());
  cloud.height = 1;
  cloud.is_dense = false;
  cloud.points.resize(scan.points.size());

  for (std::size_t i = 0; i < scan.points.size(); ++i)
  {
    const double angle =
      scan.points[i].angle * degrees_to_radians;

    cloud.points[i].x = static_cast<float>(
      scan.points[i].range * std::cos(angle));

    cloud.points[i].y = static_cast<float>(
      scan.points[i].range * std::sin(angle));

    cloud.points[i].z = 0.0F;
  }

  pcl::toROSMsg(cloud, output);
}


void command_topic_thread()
{
  auto command_node =
    std::make_shared<LidarCommandSubscriber>();

  rclcpp::spin(command_node);
}


int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  auto node =
    rclcpp::Node::make_shared("cspc_lidar");

  node_lidar.lidar_general_info.port =
    node->declare_parameter<std::string>(
      "port",
      "/dev/ttyUSB0");

  node_lidar.lidar_general_info.m_SerialBaudrate =
    node->declare_parameter<int>(
      "baudrate",
      230400);

  node_lidar.lidar_general_info.frame_id =
    node->declare_parameter<std::string>(
      "frame_id",
      "laser_link");

  node_lidar.lidar_general_info.version =
    node->declare_parameter<int>(
      "version",
      4);

  RCLCPP_INFO(
    node->get_logger(),
    "Port: %s",
    node_lidar.lidar_general_info.port.c_str());

  RCLCPP_INFO(
    node->get_logger(),
    "Baudrate: %d",
    node_lidar.lidar_general_info.m_SerialBaudrate);

  RCLCPP_INFO(
    node->get_logger(),
    "Frame ID: %s",
    node_lidar.lidar_general_info.frame_id.c_str());

  RCLCPP_INFO(
    node->get_logger(),
    "Version: %d",
    node_lidar.lidar_general_info.version);

  auto error_publisher =
    node->create_publisher<std_msgs::msg::String>(
      "lsd_error",
      10);

  auto laser_publisher =
    node->create_publisher<sensor_msgs::msg::LaserScan>(
      "scan",
      10);

  auto point_cloud_publisher =
    node->create_publisher<sensor_msgs::msg::PointCloud2>(
      "point_cloud",
      10);

  std::thread command_thread(command_topic_thread);

  node_start();

  while (rclcpp::ok())
  {
    rclcpp::spin_some(node);

    if (node_lidar.lidar_status.lidar_abnormal_state != 0)
    {
      std_msgs::msg::String error_message;

      if (
        node_lidar.lidar_status.lidar_abnormal_state &
        0x01)
      {
        error_message.data = "Lidar is trapped";
        error_publisher->publish(error_message);
        RCLCPP_ERROR(
          node->get_logger(),
          "Abnormal state: lidar is trapped");
      }

      if (
        node_lidar.lidar_status.lidar_abnormal_state &
        0x02)
      {
        error_message.data =
          "Lidar frequency is abnormal";
        error_publisher->publish(error_message);
        RCLCPP_ERROR(
          node->get_logger(),
          "Abnormal state: frequency error");
      }

      if (
        node_lidar.lidar_status.lidar_abnormal_state &
        0x04)
      {
        error_message.data = "Lidar is blocked";
        error_publisher->publish(error_message);
        RCLCPP_ERROR(
          node->get_logger(),
          "Abnormal state: lidar is blocked");
      }

      node_lidar.serial_port->write_data(end_lidar, 4);
      node_lidar.lidar_status.lidar_ready = false;

      std::this_thread::sleep_for(
        std::chrono::seconds(1));

      continue;
    }

    LaserScan scan;

    if (!data_handling(scan))
    {
      continue;
    }

    auto scan_message =
      std::make_unique<sensor_msgs::msg::LaserScan>();

    scan_message->header.stamp.sec =
      static_cast<std::int32_t>(
        scan.stamp / 1000000000ULL);

    scan_message->header.stamp.nanosec =
      static_cast<std::uint32_t>(
        scan.stamp % 1000000000ULL);

    scan_message->header.frame_id =
      node_lidar.lidar_general_info.frame_id;

    scan_message->angle_min =
      scan.config.min_angle;

    scan_message->angle_max =
      scan.config.max_angle;

    scan_message->angle_increment =
      scan.config.angle_increment;

    scan_message->scan_time =
      scan.config.scan_time;

    scan_message->time_increment =
      scan.config.time_increment;

    scan_message->range_min =
      scan.config.min_range;

    scan_message->range_max =
      scan.config.max_range;

    scan_message->ranges.resize(scan.points.size());
    scan_message->intensities.resize(
      scan.points.size());

    for (
      std::size_t i = 0;
      i < scan.points.size();
      ++i)
    {
      scan_message->ranges[i] =
        scan.points[i].range;

      scan_message->intensities[i] =
        scan.points[i].intensity;
    }

    sensor_msgs::msg::PointCloud2 point_cloud_message;

    scan_to_point_cloud(
      scan,
      point_cloud_message,
      node_lidar.lidar_general_info.frame_id);

    point_cloud_message.header =
      scan_message->header;

    laser_publisher->publish(*scan_message);
    point_cloud_publisher->publish(
      point_cloud_message);
  }

  node_lidar.serial_port->write_data(end_lidar, 4);

  rclcpp::shutdown();

  if (command_thread.joinable())
  {
    command_thread.join();
  }

  return 0;
}