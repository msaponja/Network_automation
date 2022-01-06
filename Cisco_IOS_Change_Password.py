import time
from netmiko import ConnectHandler
from datetime import datetime
import netmiko
from tqdm import tqdm
import csv
import getpass
import string
import secrets

#Opening CSV file which is formated as IP,Hostname,local_username
with open("target_devices.csv", "r") as f:
    reader = csv.reader(f)

    unsuccessful_devices = list()

    #username = getpass.getpass("Enter your username:")
    #password = getpass.getpass("Enter your password:")
    i = 0
    # Initializing connection to end devices
    for row in tqdm(reader, initial=1):
        alphabet = string.ascii_letters + string.digits
        user_exec_password = ''.join(secrets.choice(alphabet) for i in range(10))
        privileged_exec_password = ''.join(secrets.choice(alphabet) for i in range(10))

        cisco_device = {
            "device_type": "cisco_ios",
            "host": row[0],
            "username": "Enter_Your_Username_Here",
            "password": "Enter_Your_Password_Here",
            "port": 22,
            "secret": "Enter_Your_Secret_Here",
            "verbose": False
            }
        try:
            connection = netmiko.ConnectHandler(**cisco_device)

        except (netmiko.ssh_exception.NetmikoTimeoutException,netmiko.ssh_exception.NetmikoAuthenticationException):
            print(f'There has been an error while connecting to {row[1]}')
            unsuccessful_devices.append(row[1])
            continue

        connection.enable()
        commands = ["username " + row[2] + " secret " + user_exec_password,"enable secret " + privileged_exec_password,"exit"]
        connection.send_config_set(commands)
        prompt = connection.find_prompt()
        hostname = prompt[0:-1]

        with open("error", "w") as f:
            f.write("\n".join(unsuccessful_devices))

        with open("password", "a") as f1:
            f1.write(row[0]+","+row[1]+","+row[2]+","+user_exec_password+","+privileged_exec_password + "\n")

        print(f'{hostname} finished!')
        connection.disconnect()
    print("Local password change is complete!")

