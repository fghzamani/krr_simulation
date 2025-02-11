from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, ExecuteProcess, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare  

def generate_launch_description():
    # Get the package share directory
    package_share_dir = FindPackageShare("mirte_navigation").find("mirte_navigation")

    # Define relative paths for the map and params file
    map_file = PathJoinSubstitution([package_share_dir, "maps", "map.yaml"])
    params_file = PathJoinSubstitution([package_share_dir, "params", "mirte_nav2_params.yaml"])

    # Localization launch
    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare("nav2_bringup"), "launch", "localization_launch.py"
        ])),
        launch_arguments={"map": map_file}.items()
    )

    # Navigation launch
    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare("nav2_bringup"), "launch", "navigation_launch.py"
        ])),
        launch_arguments={
            "map": map_file,
            "params_file": params_file
        }.items()
    )

    # RViz execution
    rviz_command = ExecuteProcess(
        cmd=["rviz2", "-d", PathJoinSubstitution([
            FindPackageShare("nav2_bringup"), "rviz", "nav2_default_view.rviz"
        ])],
        output="screen"
    )
    
    initial_pose_node = TimerAction(
        period=1.0,  # Delay in seconds before starting the initial pose node
        actions=[
            Node(
                package='mirte_navigation',
                executable='set_initial_pose',
                name='set_initial_pose',
                output='screen'
            )
        ]
    )

    return LaunchDescription([
        localization_launch,
        navigation_launch,
        rviz_command,
        initial_pose_node
    ])
