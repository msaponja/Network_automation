from netmiko import ConnectHandler
from datetime import datetime
import netmiko
from tqdm import tqdm
import csv
import getpass

# Opening CSV file which is formated as IP,Hostname,local_username
with open("target_devices.csv", "r") as f:
    reader = csv.reader(f)

    unsuccessful_devices = list()

    # Use getpass to hide you credentials (This only applies if you are starting script from a terminal like cmd)
    # username = getpass.getpass("Enter your username:")
    # password = getpass.getpass("Enter your password:")
    username = input("Enter your username:")
    password = input("Enter your password:")

# Initializing connection to end devices (Here -> Host=IP)
# TQDM added for the purpose of the progress bar
    for row in tqdm(reader, initial=1):
        cisco_device = {
                "device_type":"cisco_ios",
                "host":row[0],
                "username":username,
                "password":password,
                "port":22,
                "secret":"cisco",
                "verbose":False
            }
        try:
            connection = netmiko.ConnectHandler(**cisco_device)

        except (netmiko.ssh_exception.NetmikoTimeoutException,netmiko.ssh_exception.NetmikoAuthenticationException):
            print()
            unsuccessful_devices.append(row[1])
            continue

        connection.enable()

        output = connection.send_command("show run")
        prompt = connection.find_prompt()
        hostname = prompt[0:-1]

        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day

        filename = f'{hostname}_{year}_{month}_{day}_backup.txt'
        with open(filename , "w") as backup:
            backup.write(output)

        with open("error", "w") as f:
            f.write("\n".join(unsuccessful_devices))

        print(f'{hostname} finished!')
        connection.disconnect()

    print("Configuration backup is complete!")

