#############################################
####    Cisco IOS Upgrade in Bulk        ####
####    Script written by UC Collabing    ####
####    https://www.uccollabing.com        ####
#############################################

import subprocess, re, time, netmiko
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException
from netmiko.ssh_exception import SSHException
from netmiko.ssh_exception import AuthenticationException
from netmiko import SCPConn
from datetime import datetime
import csv

#Important parameters that can be changed and controlled from here

with open("target_devices.csv", "r") as f:
    reader = csv.reader(f)

    #Cisco IOS 4321 Data
    new_ios_4321 = "Full_Name_IOS_Image_File"
    new_ios_4321_size = "Size_In_Bytes"
    new_ios_4321_md5 = "MD5_hash"

    copy_from = "tftp"
    copy_to = "flash:"
    tftp_ip = "TFTP_SERVER_IP"
    reload_wait_time = "400"
    auto_copy_to_flash = "Yes"
    auto_change_boot_sequence ="Yes"
    auto_reload = "Yes"

    #########################################

    #Creating the CSV files for pre and post upgrade#

    #clearing the old data from the CSV file and writing the headers
    f = open("pre_upgrade.csv", "w+")
    f.write("IP Address, Hostname, Uptime, Current_Version, Current_Image, Serial_Number, Device_Model, Device_Memory, Start_Time")
    f.write("\n")
    f.close()


    #clearing the old data from the CSV file and writing the headers
    f = open("post_upgrade.csv", "w+")
    f.write("IP Address, Hostname, Uptime, Current_Version, Current_Image, Serial_Number, Device_Model, Device_Memory, End_Time")
    f.write("\n")
    f.close()


    #clearing the old data from the logs file and writing the headers
    f = open("logs.txt", "w+")
    f.close()


    now = datetime.now()
    logs_time = now.strftime("%H:%M:%S")

    username = input("Enter your username: ")
    password = input("Enter your password: ")
    secret = input("Enter your secret: ")

    #############################################################################################################################

    for row in reader:
        cisco = {
            "device_type": "cisco_ios",
            "ip": row[0],
            "username": username,
            "password": password,
            "secret": secret,
            "port" : 22,
            "fast_cli" : False,
            "verbose" : False
        }

        try:
            net_connect = ConnectHandler(**cisco)

        except (NetMikoTimeoutException, AuthenticationException, SSHException, ValueError, TimeoutError, ConnectionError,
                ConnectionResetError, OSError):
            now = datetime.now()
            logs_time = now.strftime("%H:%M:%S")
            f = open("logs.txt", "a")
            f.write("" + logs_time + ": " + row[1] + " device login issue " + "\n")
            f.close()
            print("Wrong Log-in credentials!")
            break

        net_connect.enable()

        # execute show version on router and save output to output object
        sh_ver_output = net_connect.send_command("show version")

        #finding version in output using regular expressions
        regex_version = re.compile(r'Cisco\sIOS\sSoftware.+Version\s([^,]+)')
        version = regex_version.findall(sh_ver_output)
        version = version[0]

        # Type your version or versions here
        if version == "16.12.4":
            print(f"The IOS version for {row[1]} is up to date!")
            f = open("already_upgraded.csv", "a")
            f.write(row[1])
            f.write("\n")
            f.close()
            pass

        else:

            def preupgrade():

                now = datetime.now()
                logs_time = now.strftime("%H:%M:%S")
                print("" + logs_time + ": " + row[1] + " Checking this device, Collecting pre-report ")
                #handling exceptions errors

                #list where informations will be stored
                pre_upgrade_devices = []

                #finding hostname in output using regular expressions
                regex_hostname = re.compile(r'(\S+)\suptime')
                hostname = regex_hostname.findall(sh_ver_output)

                #finding uptime in output using regular expressions
                regex_uptime = re.compile(r'\S+\suptime\sis\s(.+)')
                uptime = regex_uptime.findall(sh_ver_output)
                uptime = str(uptime).replace(',' ,'').replace("'" ,"")
                uptime = str(uptime)[1:-1]

                #finding serial in output using regular expressions
                regex_serial = re.compile(r'Processor\sboard\sID\s(\S+)')
                serial = regex_serial.findall(sh_ver_output)

                #finding ios image in output using regular expressions
                regex_ios = re.compile(r'System\simage\sfile\sis\s"([^ "]+)')
                ios = regex_ios.findall(sh_ver_output)

                #finding model in output using regular expressions
                regex_model = re.compile(r'[Cc]isco\s(\S+).*memory.')
                model = regex_model.findall(sh_ver_output)


                #finding the router's memory using regular expressions
                regex_memory = re.search(r'with (.*?) bytes of memory', sh_ver_output).group(1)
                memory = regex_memory


                #append results to table [hostname,uptime,version,serial,ios,model]
                pre_upgrade_devices.append([row[0],hostname[0],uptime,version[0],ios[0],serial[0],model[0],memory,logs_time])


                #print all results (for all routers) on screen
                for i in pre_upgrade_devices:
                    i = ", ".join(i)
                    f = open("pre_upgrade.csv", "a")
                    f.write(i)
                    f.write("\n")
                    f.close()

                    now = datetime.now()
                    logs_time = now.strftime("%H:%M:%S")

                    f = open("logs.txt", "a")
                    f.write("" + logs_time + ": " + row[1] + " collecting pre upgrade report " + "\n" )
                    f.close()


                if auto_copy_to_flash == "Yes":

                    #Check necessary space on Flash:
                    output = net_connect.send_command("show flash:")
                    output = re.findall(r"\w+(?= bytes available)", output)
                    output = ", ".join(output)


                    if model[0] == "ISR4321/K9":

                        check_if_space_available = int(output) - int(new_ios_4321_size)

                        if (check_if_space_available) > 0:
                            now = datetime.now()
                            logs_time = now.strftime("%H:%M:%S")
                            print("" + logs_time + ": " + row[1] + " Sufficient space available ")
                            f = open("logs.txt", "a")
                            f.write("" + logs_time + ": " + row[1] + " Sufficent space available" + "\n" )
                            f.close()
                            time.sleep(2)
                            pass

                        elif int(check_if_space_available) < 0:
                            now = datetime.now()
                            logs_time = now.strftime("%H:%M:%S")
                            print("" + logs_time + ": " + row[1] + " Not enough space ")
                            f = open("logs.txt", "a")
                            f.write("" + logs_time + ": " + row[1] + " not enough space" + "\n" )
                            f.close()
                            return

                        # TFTP part
                        tftp_size_command = ["ip tftp blocksize 8192"]
                        net_connect.send_config_set(tftp_size_command)
                        command = "copy " + copy_from + " " + copy_to
                        start_time = datetime.now()
                        output = net_connect.send_command_timing(command, strip_prompt=False, strip_command=False,
                                                                 delay_factor=1)
                        now = datetime.now()
                        logs_time = now.strftime("%H:%M:%S")
                        print("" + logs_time + ": " + row[1] + " " + output)
                        command = tftp_ip
                        output = net_connect.send_command(command, expect_string=r']?')

                        now = datetime.now()
                        logs_time = now.strftime("%H:%M:%S")
                        print("" + logs_time + ": " + row[1] + " " + output)

                        command = new_ios_4321
                        output = net_connect.send_command(command, expect_string=r']?')
                        now = datetime.now()
                        logs_time = now.strftime("%H:%M:%S")
                        print("" + logs_time + ": " + row[1] + " " + output)

                        start_time = datetime.now()

                        # delay factor = 1 -> aprox 100 seconds. Will continue if the download finishes prior to that time!

                        command = new_ios_4321
                        output = net_connect.send_command_timing(command, delay_factor=54, strip_prompt=False,
                                                                 strip_command=False)
                        end_time = datetime.now()
                        now = datetime.now()
                        logs_time = now.strftime("%H:%M:%S")
                        print("" + logs_time + ": " + row[1] + " " + output)
                        total_time = end_time - start_time
                        print(f"Data Transfer Duration: {total_time}")

                        if re.search(r'\sbytes copied\b',output):

                            logs_time = now.strftime("%H:%M:%S")
                            print("" + logs_time + ": " + row[1] + " File copied successfully ")
                            f = open("logs.txt", "a")
                            f.write("" + logs_time + ": " + row[1] + " file copied successfully" + "\n" )
                            f.close()

                            command = "verify /md5 flash:" + new_ios_4321
                            now = datetime.now()
                            logs_time = now.strftime("%H:%M:%S")

                            output = net_connect.send_command_timing(command, strip_prompt=False, strip_command=False, delay_factor=5)
                            print("" + logs_time + ": " + row[1] + "Calculated MD5 is : " + output + "\n" "Expected MD5 is : " + new_ios_4321_md5 )
                            try:
                                output = re.search(' = (\w+)',output)
                                print(output)

                            except AttributeError:
                                output = re.search(' = (\w+)',output), output.group(1)


                            if new_ios_4321_md5 == str(output.group(1)):

                                now = datetime.now()
                                logs_time = now.strftime("%H:%M:%S")
                                print("" + logs_time + ": " + row[1] + " MD5 checksum verified ")

                                f = open("logs.txt", "a")
                                f.write("" + logs_time + ": " + row[1] + " MD5 checksum verified" + "\n" )
                                f.close()
                                pass

                            elif new_ios_4321_md5 != str(output.group(1)):
                                now = datetime.now()
                                logs_time = now.strftime("%H:%M:%S")
                                print("" + logs_time + ": " + row[1] + " MD5 checksum mismatch ")
                                f = open("logs.txt", "a")
                                f.write("" + logs_time + ": " + row[1] + " MD5 checksum mismatch" + "\n" )
                                f.close()
                                return

                        elif re.search(r'\%Error copying\b',output):
                            now = datetime.now()
                            logs_time = now.strftime("%H:%M:%S")
                            print("" + logs_time + ": " + row[1] + " Error copying the file ")
                            f = open("logs.txt", "a")
                            f.write("" + logs_time + ": " + row[1] + " error copying file" + "\n" )
                            f.close()
                            return

                        elif re.search(r'\%Error opening\b',output):
                            now = datetime.now()
                            logs_time = now.strftime("%H:%M:%S")
                            print("" + logs_time + ": " + row[1] + " File does not exist ")
                            f = open("logs.txt", "a")
                            f.write("" + logs_time + ": " + row[1] + " file does not exist" + "\n" )
                            f.close()
                            return

                        elif re.search(r'\bAccessing',output):
                            now = datetime.now()
                            logs_time = now.strftime("%H:%M:%S")
                            print("" + logs_time + ": " + row[1] + " Please check your TFTP/SCP service/network network connectivity ")
                            f = open("logs.txt", "a")
                            f.write("" + logs_time + ": " + row[1] + " check your TFTP/SCP service/network network connectivity" + "\n" )
                            f.close()
                            return


                if auto_change_boot_sequence == "Yes":

                    remove_boot = "no boot system"
                    remove_boot = net_connect.send_config_set(remove_boot)

                    add_boot1 = "boot system flash:" + new_ios_4321
                    add_boot1 = net_connect.send_config_set(add_boot1)

                    add_boot2 =  "boot system " + version
                    add_boot2 = net_connect.send_config_set(add_boot2)

                    now = datetime.now()
                    logs_time = now.strftime("%H:%M:%S")
                    print("" + logs_time + ": " + row[1] + " Boot sequence changed ")

                    command = "wr mem"
                    write_config = net_connect.send_command_timing(command, strip_prompt=False, strip_command=False, delay_factor=2)

                    command = ""
                    write_config = net_connect.send_command_timing(command, strip_prompt=False, strip_command=False, delay_factor=2)

                    now = datetime.now()
                    logs_time = now.strftime("%H:%M:%S")
                    print("" + logs_time + ": " + row[1] + " Configuration saved ")
                    f = open("logs.txt", "a")
                    f.write("" + logs_time + ": " + row[1] + " configuration saved" + "\n" )
                    f.close()



                elif auto_change_boot_sequence == "No":
                    now = datetime.now()
                    logs_time = now.strftime("%H:%M:%S")
                    print("" + logs_time + ": " + row[1] + " Please change the boot sequence manually! and proceed with reload ")
                    f = open("logs.txt", "a")
                    f.write("" + logs_time + ": " + row[1] + " Please change the boot sequence manually! and proceed with reload" + "\n" )
                    f.close()
                    return


                if auto_reload == "Yes":

                    try:

                        confirm_reload = net_connect.send_command('reload', expect_string='[confirm]')
                        confirm_reload = net_connect.send_command("\n")
                        logs_time = now.strftime("%H:%M:%S")
                        f = open("logs.txt", "a")
                        f.write("" + logs_time + ": " + row[1] + " Reload command sent" + "\n" )
                        f.close()
                        print("" + logs_time + ": " + row[1] + " Sending reload command ")

                    except Exception as e:
                        print(e)
                        f = open("logs.txt", "a")
                        f.write("" + logs_time + ": " + row[1] + " Reload command sent" + "\n" )
                        f.close()
                        print("" + logs_time + ": " + row[1] + " Sending reload command ")



                elif auto_reload== "No":

                    now = datetime.now()
                    logs_time = now.strftime("%H:%M:%S")
                    print("" + logs_time + ": " + row[1] + " Please reload the router manually ")
                    f = open("logs.txt", "a")
                    f.write("" + logs_time + ": " + row[1] + " Please reload the router manually" + "\n" )
                    f.close()
                    return

            preupgrade()

            def sleeptime():
                now = datetime.now()
                logs_time = now.strftime("%H:%M:%S")
                print("" + logs_time + ": Wait time activated, please wait for " + str(reload_wait_time) + " seconds")
                time.sleep(int(reload_wait_time))

            sleeptime()

            def postupgrade():
                now = datetime.now()
                logs_time = now.strftime("%H:%M:%S")
                print("" + logs_time + ": " + row[1] + " Checking this device, Collecting post-report ")

                try:
                    net_connect = ConnectHandler(**cisco)

                except (NetMikoTimeoutException, AuthenticationException, SSHException, ValueError, TimeoutError, ConnectionError, ConnectionResetError):
                    now = datetime.now()
                    logs_time = now.strftime("%H:%M:%S")
                    f = open("logs.txt", "a")
                    f.write("" + logs_time + ": " + row[1] + " device login issue " + "\n" )
                    f.close()
                    return

                try:
                    net_connect.enable()

                #handling exceptions errors
                except (NetMikoTimeoutException, AuthenticationException, SSHException, ValueError, TimeoutError, ConnectionError, ConnectionResetError, OSError):
                    now = datetime.now()
                    logs_time = now.strftime("%H:%M:%S")
                    f = open("logs.txt", "a")
                    f.write("" + logs_time + ": " + row[1] + " device login issue " + "\n" )
                    f.close()
                    return

                #list where informations will be stored
                post_upgrade_devices = []

                # execute show version on router and save output to output object
                sh_ver_output = net_connect.send_command('show version')

                #finding hostname in output using regular expressions
                regex_hostname = re.compile(r'(\S+)\suptime')
                hostname = regex_hostname.findall(sh_ver_output)

                #finding uptime in output using regular expressions
                regex_uptime = re.compile(r'\S+\suptime\sis\s(.+)')
                uptime = regex_uptime.findall(sh_ver_output)
                uptime = str(uptime).replace(',' ,'').replace("'" ,"")
                uptime = str(uptime)[1:-1]


                #finding version in output using regular expressions
                regex_version = re.compile(r'Cisco\sIOS\sSoftware.+Version\s([^,]+)')
                version = regex_version.findall(sh_ver_output)

                #finding serial in output using regular expressions
                regex_serial = re.compile(r'Processor\sboard\sID\s(\S+)')
                serial = regex_serial.findall(sh_ver_output)

                #finding ios image in output using regular expressions
                regex_ios = re.compile(r'System\simage\sfile\sis\s"([^ "]+)')
                ios = regex_ios.findall(sh_ver_output)

                #finding model in output using regular expressions
                regex_model = re.compile(r'[Cc]isco\s(\S+).*memory.')
                model = regex_model.findall(sh_ver_output)


                #finding the router's memory using regular expressions
                regex_memory = re.search(r'with (.*?) bytes of memory', sh_ver_output).group(1)
                memory = regex_memory

                end_time = datetime.now()
                #append results to table [hostname,uptime,version,serial,ios,model]
                post_upgrade_devices.append([row[0], hostname[0],uptime,version[0],ios[0], serial[0],model[0],memory,end_time.strftime("%H:%M %d-%m-%y")])


            #print all results (for all routers) on screen
                for i in post_upgrade_devices:
                    i = ", ".join(i)
                    f = open("post_upgrade.csv", "a")
                    f.write(i)
                    f.write("\n")
                    f.close()

                    f = open("logs.txt", "a")
                    f.write("" + logs_time + ": " + row[1] + " collecting post upgrade report " + "\n" )
                    f.close()

            postupgrade()




