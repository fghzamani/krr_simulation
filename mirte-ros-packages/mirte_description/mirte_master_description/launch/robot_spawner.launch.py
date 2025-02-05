import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, RegisterEventHandler, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
    TextSubstitution,
)
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterFile

def generate_launch_description():
    
    
    model_paths = [
        os.path.join(get_package_share_directory('plasys_house_world'), 'models'),     
        
    ]

    gazebo_model_path = ":".join(model_paths)
    
    world_file = os.path.join(get_package_share_directory('plasys_house_world'), 'worlds','plasys_house', 'KRR_Course_Small_house.world')
    
    prefix_arg = DeclareLaunchArgument(
            "frame_prefix",
            default_value="",
            description="An arbitrary prefix to add to the published tf2 frames. Defaults to the empty string.",
        )

    use_sim_time_arg = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='Use simulation time'
    )

    
    
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    
    pkg_name = 'mirte_master_description'
    xacro_file_name = 'mirte_master.xacro'

    xacro_file_path = os.path.join(
        get_package_share_directory(pkg_name),
        'urdf',
        xacro_file_name
    )

    # Convert xacro to URDF on-the-fly
    
    robot_description_content = Command(
        [
            FindExecutable(name="xacro"),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare(pkg_name),
                    "urdf",
                    xacro_file_name,
                ]
            ),
            " ",
            "use_sim_time:=", LaunchConfiguration("use_sim_time"),
        ]
    )   
    
    robot_description = {
        "robot_description": robot_description_content,
        "frame_prefix": LaunchConfiguration("frame_prefix"),
    }

    # Launch the Gazebo server
    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gzserver.launch.py')]
        ),
        launch_arguments={'world': world_file, 'verbose': 'true'}.items()
    )
    
    gazebo_client = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gzclient.launch.py')]
        )
    )

    # Robot State Publisher: Provide the processed URDF from xacro
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[robot_description],
        output='screen'
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'my_robot',
            '-topic', 'robot_description'
        ],
        output='screen'
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )
    
    joint_state_publisher = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        output="screen",
    )

    robot_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
#            "pid_wheels_controller",
            "mirte_base_controller",
            "mirte_arm_controller",
            "mirte_gripper_controller"
        ],
    )
    
    # artificial_map = Node(
    # package='tf2_ros',
    # executable='static_transform_publisher',
    # output='screen',
    # name = 'link_broadcast',
    # arguments=['0', '0', '0', '0', '0', '0', '1', 'map', 'odom'], #check names
    # )

    return LaunchDescription([
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[joint_state_broadcaster_spawner],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=joint_state_broadcaster_spawner,
                on_exit=[robot_controller_spawner],
            )
        ),
        SetEnvironmentVariable(name='GAZEBO_MODEL_PATH', value=gazebo_model_path),
        prefix_arg,
        use_sim_time_arg,
        gazebo_server,
        gazebo_client,
        robot_state_publisher,
        # artificial_map,
        spawn_entity,
    ])