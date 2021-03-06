#!/usr/bin/env python3

import rospy
import os
from Listener import Listener
from task_handler.srv import *

current_dir = os.path.dirname(os.path.realpath(__file__)) + "/"
print(current_dir)
scripts = [current_dir + "RoverCommandListener.py", current_dir + "ArmCommandListener.py", current_dir + "start_stream.sh"]
running_tasks = [Listener(scripts[0], "python3"), Listener(scripts[1], "python3"), Listener(scripts[2], "bash", 1, True)]
known_tasks = ["rover_listener", "arm_listener", "camera_stream"]

def handle_task_request(req):
    response = "\n" + handle_task(req.task, req.status)

    return response

def handle_task(task, status):

    response = "Nothing happened"

    global running_tasks

    if status in [0, 1] and task in known_tasks:
        # set index for corresponding listener object in array
        i = 0

        for t in known_tasks:
            if t.partition("_")[0] in task:
                chosen_task = t
                print('task chosen:', chosen_task)
                break
            i += 1


        if status == 1:

            if running_tasks[i].start():
                response = "Started " + chosen_task
            else:
                response = "Failed to start " + chosen_task

                if running_tasks[i].is_running():
                    response += ", already running"
                else: # in this case it is worth trying to start the chosen_task
                    if running_tasks[i].start():
                        response = "Started " + chosen_task
        else:
            if len(running_tasks) >= 1 and isinstance(running_tasks[i], Listener):
                if running_tasks[i].stop():
                    response = "Stopped " + chosen_task
                else:
                    response = chosen_task + " not running, cannot terminate it"

    return response + "\n"

def task_handler_server():
    rospy.init_node('task_handler_server')
    s = rospy.Service('task_handler', HandleTask, handle_task_request)
    print("Ready to respond to task handling requests")
    rospy.spin()

if __name__ == "__main__":
    task_handler_server()
