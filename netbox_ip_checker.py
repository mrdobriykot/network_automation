import ipaddress
import click
import subprocess
from concurrent.futures import ThreadPoolExecutor
import platform
import os
from datetime import datetime



# TODO реализовать функцию сканирования IP адресов созданных в Netbox и записи их в отдельный список.
# TODO реализовать функцию сравнения списков с исключением повторных.
# TODO реализовать функцию создания из списка неповторных IP адресов в Netbox продумать можно использовать многопоточночть jinja2.
# TODO сделать прогресс бар выполнения скрипта.


@click.command()
@click.option('--iplist', "-ipl", prompt=True,
              help='Input ip address for test e.g. 192.168.0.1-55 or single IP address')
def main(iplist):
    start_time = datetime.now()
    print(convert_ranges_to_ip_list(iplist))
    print(ping_ip_addresses(convert_ranges_to_ip_list(iplist)))
    print(datetime.now() - start_time)


def convert_ranges_to_ip_list(ip_list):
    full_ip_list = []
    ip_list = ip_list.split()
    for ip_addr in ip_list:
        if "-" in ip_addr:
            a = ip_addr.replace("-", " ").split()
            if len(a[1]) > 3:
                print(a[1])
                b = [ipaddr for ipaddr in ipaddress.summarize_address_range(
                    ipaddress.IPv4Address(a[0]),
                    ipaddress.IPv4Address(a[1]))]
                for ip in b:
                    for addr in ipaddress.IPv4Network(ip):
                        full_ip_list.append(str(addr))
            else:
                if a[0][-2] == "." and len(a[1]) == 2:
                    a[1] = a[0][:(-len(a[1]) + 1)] + a[1]
                elif a[0][-2] == "." and len(a[1]) == 3:
                    a[1] = a[0][:(-len(a[1]) + 2)] + a[1]
                elif a[0][-3] == "." and len(a[1]) == 3:
                    a[1] = a[0][:(-len(a[1]) + 1)] + a[1]
                else:
                    a[1] = a[0][:-len(a[1])] + a[1]
                b = [ipaddr for ipaddr in ipaddress.summarize_address_range(
                    ipaddress.IPv4Address(a[0]),
                    ipaddress.IPv4Address(a[1]))]
                for ip in b:
                    for addr in ipaddress.IPv4Network(ip):
                        full_ip_list.append(str(addr))
        else:
            full_ip_list.append(ip_addr)

    return full_ip_list


def ping_ip_addresses(ip_list, limit=20):
    ping_yes = []
    ping_no = []

    with ThreadPoolExecutor(max_workers=limit) as executor:
        futures = {}
        for ip in ip_list:
            if platform.system().lower() == "windows":
                result = executor.submit(windows_ping_ip, ip)
            else:
                result = executor.submit(linux_ping_ip, ip)
            futures[ip] = result

        for key, value in futures.items():
            if value.result() == 0:
                ping_yes.append(key)
            else:
                ping_no.append(key)
    return ping_yes


def linux_ping_ip(list_of_ip):
    result = subprocess.run(
        ["ping", "-c", "1", list_of_ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return result.returncode


def windows_ping_ip(list_of_ip):
    result = os.popen(f"ping /n 1 {list_of_ip}").read()
    if "TTL=" in result:
        return 0
    else:
        return 1


if __name__ == '__main__':
    main()
