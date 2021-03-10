"""
latest updates:
class_0 handling in zigzag.
Deleteing logs in device after saving in PC. (Keeplogs)
validation takes any digit of phone number
"""

import subprocess
import sys
from subprocess import CalledProcessError
import os
import time
from tkinter import *
from functools import partial
import uiautomator2 as dui
import json
import threading
from tkinter.messagebox import showerror, showinfo
import pdb
import re
import logging

mo_id = 0
device_id = []
state = 1
mo_modem_check = 1
mt_modem_check = 1

current_directory = os.getcwd()
final_directory = os.path.join(current_directory, r'Modem_logs_and_Bugreport')
if not os.path.exists(final_directory):
    os.makedirs(final_directory)

logging.basicConfig(level=logging.DEBUG, filename="logs.log", filemode="w", format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')


def validation(phone_number1, number_of_attempts, duration_of_calls, gap_between_calls, phone_number2=0):
    global device_id
    error_list = []
    if not re.match("^(\d+$)", phone_number1):
        error_list.append("Invalid Dialling Number 1")
    if phone_number2 != 0:
        if not re.match("^(\d+$)", phone_number2):
            error_list.append("Invalid Dialling Number 2")
    if not re.match("(\d+$)", number_of_attempts):
        error_list.append("Invalid Number of Attempts")
    if not re.match("(\d+$)", duration_of_calls):
        error_list.append("Invalid Duration of Calls")

    if error_list:
        showinfo("Error", "\n".join(error_list))
        logging.error(f"Validation Failed: {error_list} \nExiting... ")
        sys.exit()

    device_id = check_devices()
    if device_id == 0:
        showinfo("Error", "No device connected")
        sys.exit()
    elif len(device_id) != 2:
        showinfo("Error:", "Only 1 device connected.")
        sys.exit()

    writeinputs(phone_number1, number_of_attempts, duration_of_calls, phone_number2, gap_between_calls)
    logging.info(f"Validation passed: {phone_number1} {number_of_attempts} {duration_of_calls} {phone_number2} ")


def writeinputs(phone_number1, number_of_attempts, duration_of_calls, phone_number2="", gap_between_calls=5):
    dict1 = {'phone_number1': phone_number1, 'phone_number2': phone_number2, 'number_of_attempts': number_of_attempts,
             'duration_of_calls': duration_of_calls, 'gap_between_calls': gap_between_calls}
    f1 = open('dictionary.txt', 'w+')
    f1.write(json.dumps(dict1))
    f1.close()


def makereport(pass_count, fail_count, failure_details):
    w.delete('4.0', END)
    w.insert(END, '\nPass: %d\nFail: %d' % (pass_count, fail_count))
    if len(failure_details) > 0:
        w.insert(END, '\nCalls failed at timestamps:')
        w.insert(END, '\n'.join(failure_details))


def check_devices():
    global mo_id

    output = subprocess.check_output("adb devices")
    result = str(output)

    li = list(result.split("\\r\\n"))
    li1 = li[1].split("\\t")
    li2 = li[2].split("\\t")

    w.delete('1.0', END)
    if 'b\'List of devices attached\\r\\n\\r\\n\'' in result:
        w.insert(INSERT, 'No devices connected\nConnect Mo device and press ADB Devices')
        logging.info("ADB devices pressed first time.")
        return 0
    else:
        if li2[0] == '':
            mo_id = li1[0]
            w.insert(INSERT, 'Connected Devices: \nMO_device: %s' % (mo_id))
            w.insert(INSERT, '\nNow Connect MT device and press ADB devices')
            logging.info(f" {mo_id} Mo device locked")
            return mo_id
        else:
            if mo_id == 0:
                showinfo('INFO', "Insert only MO device and press ADB devices")
            if li1[0] == mo_id:
                mt_id = li2[0]
            else:
                mt_id = li1[0]
            w.insert(INSERT, 'Connected Devices: \nMO_device: %s \nMT_device: %s ' % (mo_id, mt_id))
            logging.info(f" {mo_id} {mt_id} MO and MT device locked")
            return mo_id, mt_id


def takeLogs(count, device_id):
    w.insert(INSERT, f"\nSaving bugreports....")
    logging.info("Saving bugreports..")
    os.system("adb -s %s bugreport Modem_logs_and_Bugreport/zip_MO_%d-%d" % (device_id[0], count, count + 4))
    os.system("adb -s %s bugreport Modem_logs_and_Bugreport/zip_MT_%d-%d" % (device_id[1], count, count + 4))
    w.delete('6.0', END)


def shellPIPE(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if len(err) != 0: logging.debug(err)
    if "error" in str(err) or "must be root" in str(err):
        showinfo("Error", f"{re.findall('(?<=-s )[^ ]+(?= )', cmd)} {str(err)}")
        button1.config(state="normal")
        button2.config(state="normal")
        button3.config(state="normal")
        button4.config(state="normal")
        logging.error(f"{err} \nEXITING...")
        sys.exit()
    return out


def start_modem_logs():
    global mo_modem_check, mt_modem_check
    folder1 = ""
    folder2 = ""
    out1 = str(shellPIPE("adb -s %s shell getprop ro.boot.hardware" % device_id[0]))
    out2 = str(shellPIPE("adb -s %s shell getprop ro.boot.hardware" % device_id[1]))
    fout1 = out1.strip("b\'\\r\\n")
    fout2 = out2.strip("b\'\\r\\n")
    if mo_modem_check:
        fcount = 0
        while len(folder1) == 0 and fout1 == "qcom" and fcount < 3:
            shellPIPE('adb -s %s shell start diag_mdlog_stop' % device_id[0])
            cmd1 = "adb -s %s shell start diag_mdlog_start" % device_id[0]
            shellPIPE(cmd1)
            folder1 = shellPIPE("adb -s %s shell ls /storage/emulated/0/diag_logs" % device_id[0])
            time.sleep(5)
            fcount += 1

        if len(folder1) != 0:
            logging.info("Modem logs in MO device started.")
        else:
            logging.info("Modem logs in MO device NOT started !")
            showinfo("Info",
                     "Modem logs in MO device is not starting.\nManually start the logs in MO and press OK.\nKeep saving the logs manually")
            mo_modem_check = 0

    if mt_modem_check:
        tcount = 0
        while len(folder2) == 0 and fout2 == "qcom" and tcount < 3:
            shellPIPE('adb -s %s shell start diag_mdlog_stop' % device_id[1])
            cmd2 = "adb -s %s shell start diag_mdlog_start" % device_id[1]
            shellPIPE(cmd2)
            folder2 = shellPIPE("adb -s %s shell ls /storage/emulated/0/diag_logs" % device_id[1])
            time.sleep(5)
            tcount += 1

        if len(folder2) != 0:
            logging.info("Modem logs in MT device started.")
        else:
            logging.info("Modem logs in MT device NOT started !!")
            showinfo("Info",
                     "Modem logs in MT device is not starting.\nManually start the logs in MT and press OK.\nKeep saving the logs manually")
            mt_modem_check = 0
    return mo_modem_check, mt_modem_check


def keeplogs(device_id, counter5):
    time.sleep(2)

    cmd1 = "adb -s %s shell start diag_mdlog_stop" % device_id[0]
    cmd2 = "adb -s %s shell start diag_mdlog_stop" % device_id[1]
    str(shellPIPE(cmd1))
    str(shellPIPE(cmd2))
    if mo_modem_check:
        logging.info("Saving mo modem logs...")
        w.insert(INSERT, f"\nSaving mo modem logs....")
        os.system('adb -s %s pull /storage/emulated/0/diag_logs Modem_logs_and_Bugreport/MO_log%d-%d ' % (
            device_id[0], counter5, counter5 + 4))
        w.delete('6.0', END)
        shellPIPE('adb -s %s shell rm -r /storage/emulated/0/diag_logs' % device_id[0])

    if mt_modem_check:
        logging.info("Saving mt modem logs...")
        w.insert(INSERT, f"\nSaving mt modem logs....")
        os.system('adb -s %s pull /storage/emulated/0/diag_logs Modem_logs_and_Bugreport/MT_log%d-%d ' % (
            device_id[1], counter5, counter5 + 4))
        w.delete('6.0', END)
        shellPIPE('adb -s %s shell rm -r /storage/emulated/0/diag_logs' % device_id[1])

    takeLogs(counter5, device_id)
    if mo_modem_check or mt_modem_check:
        start_modem_logs()


def deletelogs(device_id):
    cmd1 = "adb -s %s shell start diag_mdlog_stop" % device_id[0]
    cmd2 = "adb -s %s shell start diag_mdlog_stop" % device_id[1]
    str(shellPIPE(cmd1))
    str(shellPIPE(cmd2))

    time.sleep(2)
    if mo_modem_check:
        shellPIPE('adb -s %s shell rm -r /storage/emulated/0/diag_logs' % device_id[0])
        logging.info("Deleting modem logs from MO device...")
        time.sleep(2)
    if mt_modem_check:
        shellPIPE('adb -s %s shell rm -r /storage/emulated/0/diag_logs' % device_id[1])
        logging.info("Deleting modem logs from MT device...")
    time.sleep(2)
    if mo_modem_check or mt_modem_check:
        start_modem_logs()


def makezigzagmocalls(phone_number1, phone_number2, number_of_attempts, duration_of_calls, gap_between_calls):
    global state, mo_modem_check, mt_modem_check, li2
    state = 1
    li2 = []
    mt_modem_check = 1
    mo_modem_check = 1
    button1.config(state="disabled")
    button2.config(state="disabled")
    button3.config(state="disabled")
    button4.config(state="disabled")
    fail_count = 0
    pass_count = 0
    fail_count50 = 0
    counter5 = 1

    logging.info("makezigzagmocalls:")
    validation(phone_number1.get(), number_of_attempts.get(), duration_of_calls.get(), gap_between_calls.get(),
               phone_number2.get())
    shellPIPE('adb -s %s install app-uiautomator.apk && adb -s %s install app-uiautomator-test.apk' % (
        device_id[0], device_id[0]))

    w.insert(INSERT, f"\nStarting Automation....")  # update

    shellPIPE('adb -s %s root' % device_id[0])
    shellPIPE('adb -s %s root' % device_id[1])

    # deleting old logs before starting
    logging.info("Deleting old logs before starting.")
    shellPIPE('adb -s %s shell rm -r /storage/emulated/0/diag_logs' % device_id[0])
    shellPIPE('adb -s %s shell rm -r /storage/emulated/0/diag_logs' % device_id[1])

    shellPIPE("adb -s %s push atx-agent /data/local/tmp/" % device_id[0])
    shellPIPE("adb -s %s shell chmod 755 /data/local/tmp/atx-agent" % device_id[0])
    start_modem_logs()

    dialer_type = shellPIPE("adb -s %s shell pm list packages -f com.google.android.dialer" % device_id[0])
    try:
        ui = dui.connect(device_id[0])
    except Exception as connect_error:
        logging.exception(f"MO device UI automator connect error")
        showinfo("Error", f"Error:{str(connect_error)}")
        button1.config(state="normal")
        button2.config(state="normal")
        button3.config(state="normal")
        button4.config(state="normal")
        sys.exit()

    count = 0
    for i in range(0, int(number_of_attempts.get())):
        ui_automator_failure_check = 0
        if state == 1:
            ui.screen_off()
            time.sleep(2)
            logging.info(f"Iteration {i + 1}")
            if not ui.info['screenOn']:
                ui.press("power")
                time.sleep(2)
                ui.swipe(0.1, 0.9, 0.9, 0.1)
                time.sleep(2)
            ui.press("back")
            time.sleep(2)
            ui.press("home")
            time.sleep(2)
            if dialer_type:
                try:
                    if i % 2 == 0:
                        shellPIPE("adb -s %s shell service call phone 1 s16 %s" % (device_id[0], phone_number1.get()))

                        ui(className="android.widget.ImageButton",
                               resourceId="com.google.android.dialer:id/dialpad_floating_action_button").click_exists(3)

                        ui(className="android.widget.ImageButton",
                               resourceId="com.google.android.dialer:id/dialpad_voice_call_button").click_exists(3)

                        uiobj = ui(className="android.widget.ListView", resourceId="android:id/select_dialog_listview")
                        uiobj.child_by_instance(2).click()
                        logging.info("call started from SIM-1")

                    else:
                        shellPIPE("adb -s %s shell service call phone 1 s16 %s" % (device_id[0], phone_number2.get()))

                        ui(className="android.widget.ImageButton",
                               resourceId="com.google.android.dialer:id/dialpad_floating_action_button").click_exists(3)

                        ui(className="android.widget.ImageButton",
                               resourceId="com.google.android.dialer:id/dialpad_voice_call_button").click_exists(3)

                        uiobj = ui(className="android.widget.ListView", resourceId="android:id/select_dialog_listview")
                        uiobj.child_by_instance(7).click()
                        logging.info("call started from SIM-2")
                except dui.exceptions.UiObjectNotFoundError as e:
                    logging.exception(e)
                    logging.info("Call failed due to UIautomator failure")
                    ui_automator_failure_check = 1
                except Exception as e1:
                    logging.exception(e1)
                    logging.info("Call couldn't be initiated due to UIautomator failure")
                    ui_automator_failure_check = 1

            else:
                try:
                    if i % 2 == 0:
                        shellPIPE("adb -s %s shell service call phone 1 s16 %s" % (device_id[0], phone_number1.get()))
                        ui(className="android.widget.Button", resourceId="com.android.contacts:id/call_sim1").click()
                        logging.info("Call started from SIM 1")
                    else:
                        shellPIPE("adb -s %s shell service call phone 1 s16 %s" % (device_id[0], phone_number2.get()))
                        ui(className="android.widget.Button", resourceId="com.android.contacts:id/call_sim2").click()
                        logging.info("Call started from SIM 2")

                except dui.exceptions.UiObjectNotFoundError as e:
                    logging.exception(e)
                    logging.info("Call couldn't be initiated due to UIautomator failure")
                    ui_automator_failure_check = 1

                except Exception as e1:
                    logging.exception(e1)
                    logging.info("Call couldn't be initiated due to UIautomator failure")
                    ui_automator_failure_check = 1

            try:
                out1 = ""
                end_time = time.time() + 60
                time_now = 0
                while "mCallState=2" not in out1 and end_time > time_now:
                    cmd = "adb -s %s shell dumpsys telephony.registry | findstr \"mCallState\"" % device_id[1]
                    out1 = str(shellPIPE(cmd))
                    time_now = time.time()
                if "mCallState=2" in out1: logging.info("call connected")
                time.sleep(int(duration_of_calls.get()))
                logging.info(f"Sleeping time over")

                cmd = "adb -s %s shell dumpsys telephony.registry | findstr \"mCallState\"" % device_id[1]
                out1 = str(shellPIPE(cmd))

                if 'mCallState=2' in out1:
                    pass_count = pass_count + 1
                    logging.info(f"Call Passed")
                else:
                    fail_count = fail_count + 1
                    t = time.localtime()
                    current_time = time.strftime("%H:%M:%S", t)
                    if ui_automator_failure_check == 0:
                        li2.append(current_time)
                    else:
                        li2.append(f"Call failed due to UiAutomator failure at {current_time}")
                    logging.info(f"Call Failed")

                cmd = "adb -s %s shell dumpsys telephony.registry | findstr \"mCallState\"" % device_id[0]
                out1 = str(shellPIPE(cmd))

                if 'mCallState=2' in out1:
                    shellPIPE("adb -s %s shell input keyevent 6" % device_id[0])
                time.sleep(int(gap_between_calls.get()))

            except Exception as e2:
                logging.exception(e2)
                showerror("Error", f"{str(e2)}")
                button1.config(state="normal")
                button2.config(state="normal")
                button3.config(state="normal")
                button4.config(state="normal")
                sys.exit()

            w.delete('4.0', END)
            w.insert(INSERT, f"\nPass:{pass_count}\nFail:{fail_count}")
            print("Pass:%d\nFail:%d" % (pass_count, fail_count))
            f = open("Result.txt", "w+")
            f.write("Pass:%d\nFail:%d\n" % (pass_count, fail_count))
            f.write('\n'.join(li2))
            f.close()

            count = count + 1
            if count % 3 == 0:  # to clear cmd
                os.system('cls')

            if count % 5 == 0:

                print(fail_count)
                if fail_count > fail_count50:
                    keeplogs(device_id, counter5)
                    fail_count50 = fail_count

                else:
                    deletelogs(device_id)
                counter5 = counter5 + 5

            if (count) == int(number_of_attempts.get()):
                makereport(pass_count, fail_count, li2)
                cmd1 = "adb -s %s shell start diag_mdlog_stop" % device_id[0]
                cmd2 = "adb -s %s shell start diag_mdlog_stop" % device_id[1]
                str(shellPIPE(cmd1))
                str(shellPIPE(cmd2))
                os.system("adb -s %s shell start diag_mdlog_stop" % device_id[0])
                os.system("adb -s %s shell start diag_mdlog_stop" % device_id[1])
                logging.info("Program Ended.")

                button1.config(state="normal")
                button2.config(state="normal")
                button3.config(state="normal")
                button4.config(state="normal")
        else:
            button1.config(state="normal")
            button2.config(state="normal")
            button3.config(state="normal")
            button4.config(state="normal")
            os.system("adb -s %s shell start diag_mdlog_stop" % device_id[0])
            os.system("adb -s %s shell start diag_mdlog_stop" % device_id[1])
            button5.config(state="normal")
            break


def makemocalls(phone_number1, number_of_attempts, duration_of_calls, function_name, gap_between_calls):
    global state, mo_modem_check, mt_modem_check, li2
    state = 1
    li2 = []
    mt_modem_check = 1
    mo_modem_check = 1
    fail_count = 0
    pass_count = 0
    fail_count50 = 0
    counter5 = 1

    logging.info(f"{function_name}:")

    validation(phone_number1.get(), number_of_attempts.get(), duration_of_calls.get(), gap_between_calls.get())

    w.insert(INSERT, f"\nStarting Automation....")  # update

    button1.config(state="disabled")
    button2.config(state="disabled")
    button3.config(state="disabled")
    button4.config(state="disabled")

    shellPIPE('adb -s %s root' % device_id[0])
    shellPIPE('adb -s %s root' % device_id[1])

    # deleting old logs before starting
    logging.info("Deleting old logs before starting.")
    shellPIPE('adb -s %s shell rm -r /storage/emulated/0/diag_logs' % device_id[0])
    shellPIPE('adb -s %s shell rm -r /storage/emulated/0/diag_logs' % device_id[1])

    start_modem_logs()
    count = 0
    if function_name == "makevideocalls":
        shellPIPE("adb -s %s shell input keyevent 164" % device_id[0])
        shellPIPE("adb -s %s shell input keyevent 164" % device_id[1])
    for i in range(0, int(number_of_attempts.get())):
        if state == 1:
            logging.info(f"Iteration {i + 1}")
            try:
                if function_name == "makemocalls":
                    shellPIPE("adb -s %s shell am start -a android.intent.action.CALL -d tel:%d" % (
                        device_id[0], int(phone_number1.get())))
                    logging.info("Audio call Started")
                elif function_name == "makevideocalls":
                    shellPIPE(
                        "adb -s %s shell am start -a android.intent.action.CALL -d tel:%d --ei android.telecom.extra.START_CALL_WITH_VIDEO_STATE 3" % (
                            device_id[0], int(phone_number1.get())))
                    logging.info("Video call started")

                out1 = ""
                end_time = time.time() + 60
                time_now = 0
                while "mCallState=2" not in out1 and end_time > time_now:
                    cmd = "adb -s %s shell dumpsys telephony.registry | findstr \"mCallState\"" % device_id[1]
                    out1 = str(shellPIPE(cmd))
                    time_now = time.time()
                if "mCallState=2" in out1: logging.info("call connected")
                time.sleep(int(duration_of_calls.get()))
                logging.info(f"Sleep time over ")

                cmd = "adb -s %s shell dumpsys telephony.registry | findstr \"mCallState\"" % device_id[1]
                out1 = str(shellPIPE(cmd))

                if 'mCallState=2' in out1:
                    pass_count = pass_count + 1
                    logging.info(f"Call Passed")

                else:
                    fail_count = fail_count + 1
                    t = time.localtime()
                    current_time = time.strftime("%H:%M:%S", t)
                    li2.append(current_time)
                    logging.info(f"Call Failed")

                cmd = "adb -s %s shell dumpsys telephony.registry | findstr \"mCallState\"" % device_id[0]
                out1 = str(shellPIPE(cmd))

                if 'mCallState=2' in out1:
                    shellPIPE("adb -s %s shell input keyevent 6" % device_id[0])

                time.sleep(int(gap_between_calls.get()))
                w.delete('4.0', END)
                w.insert(INSERT, f"\nPass:{pass_count}\nFail:{fail_count}")
                print("Pass:%d\nFail:%d" % (pass_count, fail_count))
                f = open("Result.txt", "w+")
                f.write("Pass:%d\nFail:%d\n" % (pass_count, fail_count))
                f.write(','.join(li2))
                f.close()

                count = count + 1
                if count % 3 == 0:  # to clear cmd
                    os.system('cls')

                if count % 5 == 0:
                    if fail_count > fail_count50:
                        keeplogs(device_id, counter5)
                        fail_count50 = fail_count
                    else:
                        deletelogs(device_id)
                    counter5 = counter5 + 5

                if (count) == int(number_of_attempts.get()):
                    makereport(pass_count, fail_count, li2)
                    cmd1 = "adb -s %s shell start diag_mdlog_stop" % device_id[0]
                    cmd2 = "adb -s %s shell start diag_mdlog_stop" % device_id[1]
                    str(shellPIPE(cmd1))
                    str(shellPIPE(cmd2))
                    os.system("adb -s %s shell start diag_mdlog_stop" % device_id[0])
                    os.system("adb -s %s shell start diag_mdlog_stop" % device_id[1])
                    logging.info("Program ended")
                    button1.config(state="normal")
                    button2.config(state="normal")
                    button3.config(state="normal")
                    button4.config(state="normal")

            except Exception as mocall_error:
                logging.error(mocall_error)
                showinfo("Error:", mocall_error)
                button1.config(state="normal")
                button2.config(state="normal")
                button3.config(state="normal")
                button4.config(state="normal")
                sys.exit()
        else:
            button1.config(state="normal")
            button2.config(state="normal")
            button3.config(state="normal")
            button4.config(state="normal")
            os.system("adb -s %s shell start diag_mdlog_stop" % device_id[0])
            os.system("adb -s %s shell start diag_mdlog_stop" % device_id[1])
            button5.config(state="normal")
            break


def my_thread1():
    t1 = threading.Thread(target=makezigzagmocalls,
                          args=(phone_number1, phone_number2, number_of_attempts, duration_of_calls, gap_between_calls))
    t1.daemon = True
    t1.start()


def my_thread2():
    t2 = threading.Thread(target=makemocalls,
                          args=(phone_number1, number_of_attempts, duration_of_calls, "makemocalls", gap_between_calls))
    t2.daemon = True
    t2.start()


def my_thread3():
    t3 = threading.Thread(target=makemocalls, args=(
    phone_number1, number_of_attempts, duration_of_calls, "makevideocalls", gap_between_calls))
    t3.daemon = True
    t3.start()


def stop():
    global state
    state = 0
    button5.config(state="disabled")


master = Tk()
master.title("Call Automator")

w = Text(master, height=10, width=85)
w.grid(row=8, pady=(50, 0))
w.insert(INSERT, 'Connect Mo device and press ADB Devices')

phone_number1 = StringVar()
phone_number2 = StringVar()
number_of_attempts = StringVar()
duration_of_calls = StringVar()
gap_between_calls = StringVar()

Label(master, text='Phone Number 1').place(x=0, y=0)
Label(master, text='Phone Number 2').place(x=0, y=20)
Label(master, text='Call Attempts').place(x=0, y=40)
Label(master, text='Call Duration(in sec.)').place(x=0, y=60)
Label(master, text='Dialling Pause(in sec.)').place(y=0, x=550)
e1 = Entry(master, width=50, textvariable=phone_number1).grid(row=0)
e2 = Entry(master, width=50, textvariable=phone_number2).grid(row=1)
e3 = Entry(master, width=50, textvariable=number_of_attempts).grid(row=2)
e4 = Entry(master, width=50, textvariable=duration_of_calls).grid(row=3)
e4 = Entry(master, width=20, textvariable=gap_between_calls).place(y=20, x=550)

check_devices = partial(check_devices)
my_thread1 = partial(my_thread1)
my_thread2 = partial(my_thread2)
my_thread3 = partial(my_thread3)
stop = partial(stop)

button1 = Button(master, text='Connect ADB device', width=23, height=2, command=check_devices)
button1.place(x=0, y=80)
button2 = Button(master, text='Automate Voice calls', width=23, height=2, command=my_thread2)
button2.place(x=170, y=80)
button3 = Button(master, text="Automate ZigZag calls", width=23, height=2, command=my_thread1)
button3.place(y=80, x=510)
button4 = Button(master, text='Automate Video calls', width=23, height=2, command=my_thread3)
button4.place(y=80, x=340)
button5 = Button(master, text='Stop', command=stop)
button5.place(y=45, x=600)

try:
    f2 = open('dictionary.txt', 'r')
except FileNotFoundError:
    pass
else:
    if os.stat("dictionary.txt").st_size != 0:
        dict2 = json.loads(f2.read())
        phone_number1.set(dict2["phone_number1"])
        phone_number2.set(dict2["phone_number2"])
        number_of_attempts.set(dict2["number_of_attempts"])
        duration_of_calls.set(dict2["duration_of_calls"])
        gap_between_calls.set(dict2["gap_between_calls"])
    f2.close()

master.mainloop()