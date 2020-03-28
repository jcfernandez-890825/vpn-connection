import ipaddress
import os
import socket
from itertools import compress
from multiprocessing import Pool

from systemd import journal as sys_journal
from urllib3 import PoolManager as URL3PoolManager
from urllib3.exceptions import MaxRetryError, ConnectTimeoutError, NewConnectionError


def _check_server(address, port):
    # Create a TCP socket
    with socket.socket() as s:
        s.settimeout(3)
        try:
            s.connect((address, port))
            value = True
        except socket.error as e:
            # print(address, port, e)
            value = False

    return value


def _check_dns_response(dns_name):
    try:
        return bool(socket.gethostbyname(dns_name))
    except socket.gaierror:
        print('No hay DNS, llamar a Carly')
    except socket.error as e:
        print(dns_name, e)
        return False


def _check_dns(addr):
    return _check_server(addr, 53)


def _check_dns_subnet(ip_itr) -> iter:
    """
    Checks if DNS TCP port #53 is open foreach IP in subnet_itr
    Returns an iterator having True if DNS TCP port #53 is open or False for each member:
    :param ip_itr:
    :return iter:
    """
    return compress(
        ip_itr, Pool(os.cpu_count()).map(_check_dns, ip_itr)
    )


def _get_dns_ip_lst(ip_itr) -> list:
    return list(_check_dns_subnet(ip_itr))


def _get_ip_lst(dns_subnet_str):
    return set([
        str(ipv4)
        for ipv4 in ipaddress.ip_network(dns_subnet_str)
    ][1:-1])


def get_dns_entries_subnet_lst():
    journal = sys_journal.Reader()
    journal.this_boot()
    journal.log_level(sys_journal.LOG_INFO)

    dns_subnet_set = set()

    # Get subnet list form DNS entries
    for entry in journal:
        msg = entry['MESSAGE']
        if 'arpa' in msg:
            msg = msg.split()[-1].replace('.in-addr.arpa', '')
            dot_count = msg.count('.') - 1
            if 2 > dot_count > 0:
                dns_subnet_set |= _get_ip_lst(
                    f"{'.'.join(reversed(msg.split('.')))}{'.0' * dot_count}/{32 - dot_count * 8}"
                )

    # Get host IP with TCP DNS port open
    return _get_dns_ip_lst(dns_subnet_set)


def check_gtw_autoticket():
    return any(
        _check_server(ip, 53)
        for ip in ('157.16.1.10', '192.168.12.6')
    )


def check_url(url, response_data=None, redirect=False):
    http = URL3PoolManager()
    try:
        with http.request(
            'GET', url,
            preload_content=False, timeout=5.0, retries=2, redirect=redirect
        ) as response:
            if response.status == 200:
                if response_data:
                    if response.data == b'success\n':
                        return True
                    else:
                        print(
                            'Hay conexión, pero no hay internet, '
                            'chequear si está el Portal de ETECSA o el de Luis con un celular, '
                            'arreglar el Portal de ETECSA usando el botón de Autotickets en el Firefox, '
                            'o llamar a Carly'
                        )
                        return False
                else:
                    return True
            else:
                print(f'HTTP error code {response.status}')
                return False
    except (ConnectTimeoutError, MaxRetryError, NewConnectionError) as e:
        if 'Name or service not known' in str(e):
            print('No hay DNS, llamar a Carly')
        elif 'Network is unreachable' in str(e):
            print('La red está caída, llamar a Carly')
        elif 'TimeoutError' in str(e):
            print(
                'No hay navegación, '
                'chequear si está el Portal de ETECSA o el de Luis con un celular, '
                'arreglar usando el botón de Autotickets en el Firefox, '
                'o llamar a Carly'
            )
        else:
            print(e)
        return False


def check_connectivity():
    return all((
        # Check gateway and Auto-tickets
        check_gtw_autoticket(),
        # Check host us-free-02.protonvpn.com DNS resolution
        _check_dns_response('us-free-02.protonvpn.com'),
        # Check Internet connectivity
        check_url('http://detectportal.firefox.com/success.txt', b'success\n', redirect=True),
    ))
