import time
import os
from datetime import datetime

from utils.nmtools import NetMngVPNConn
from utils.utils import check_connectivity


def main():
    conn_name = 'Luis-Internet'
    vpn_name = 'us-free-02.protonvpn.com.udp'
    vpn_conn = NetMngVPNConn(conn_name, vpn_name)

    bad_conn = False

    print(f'{datetime.now()} - Iniciando, chequeando si hay Internet')

    if vpn_conn.conn_activated:
        print(f'{datetime.now()} - VPN conectada')
        os.system('mpv --no-terminal /home/batman/MyBash/Batwave.Alert.mp3')

    # Repeat forever
    while True:
        # Check gateway and Auto-tickets
        # and
        # Check Internet connectivity
        # and
        # Check host us-free-02.protonvpn.com DNS resolution
        if check_connectivity():
            if bad_conn:
                bad_conn = False
                print(f'{datetime.now()} - La conexión se restableció')

            if not vpn_conn.conn_activated:
                print(f'{datetime.now()} - Iniciando la conexión VPN')
                # Connect VPN
                if vpn_conn.connect():
                    print(f'{datetime.now()} - VPN conectada')
                    os.system('mpv --no-terminal /home/batman/MyBash/Batwave.Alert.mp3')
                else:
                    print(f'{datetime.now()} - La conexión VPN tardó demasiado, volviendo a intentar')
        else:
            if not bad_conn:
                print(f'{datetime.now()} - Se cayó la conexión')
                bad_conn = True

            # Disconnect VPN
            if vpn_conn.disconnect():
                os.system('mpv --no-terminal --length=3.5 /home/batman/MyBash/Nuke.Alert.Sound.mp3')

        time.sleep(3)


if __name__ == '__main__':
    main()
