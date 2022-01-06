import time

from netmiko import ConnectHandler
from datetime import datetime
import netmiko
from tqdm import tqdm
import csv
import getpass

start = time.time()

# Opening CSV file which is formated as IP,Hostname,local_username
with open("target_devices.csv", "r") as f:
    reader = csv.reader(f)

    unsuccessful_devices = list()

    #username = getpass.getpass("Enter your username:")
    #password = getpass.getpass("Enter your password:")
    i = 0
    # Initializing connection to end devices
    for row in tqdm(reader, initial=1):
        cisco_device = {
                "device_type":"cisco_ios",
                "host":row[0],
                "username":"Enter_Your_Username_Here",
                "password":"Enter_Your_Password_Here",
                "port":22,
                "secret":"Enter_Your_Secret_Here",
                "verbose":False
            }
        try:
            connection = netmiko.ConnectHandler(**cisco_device)

        except (netmiko.ssh_exception.NetmikoTimeoutException,netmiko.ssh_exception.NetmikoAuthenticationException):
            print(f'There has been an error while connecting to {row[1]}!')
            unsuccessful_devices.append(row[1])
            continue

        connection.enable()

        connection.send_command("clear access-list counters")
        connection.send_command("clear arp-cache")
        connection.send_command(command_string="clear counters",expect_string=r"]?",strip_prompt=False,strip_command=False)
        connection.send_command("clear ip accounting")
        connection.send_command(command_string="clear logging",expect_string=r"]?",strip_prompt=False,strip_command=False)

        prompt = connection.find_prompt()
        hostname = prompt[0:-1]

        i = i + 1

        with open("error", "w") as f:
            f.write("\n".join(unsuccessful_devices))

        print(f'{hostname} finished!')
        connection.disconnect()
    print("Configuration clean is complete!")
    end = time.time()
    print(f'For {i} devices, the time to complete is {round(end-start,2)} !')


