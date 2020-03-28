import NetworkManager
import time
import sys


class NetMngConn(object):
    def __init__(self, conn_name):
        # Set Connection name
        self._conn_name = conn_name

        # Get Connections Dictionary
        conn_dct = {
            conn.GetSettings()['connection']['id']: conn
            for conn in NetworkManager.Settings.ListConnections()
        }
        self._conn_dct = conn_dct

        # Set Connection Instance
        self._conn = conn_dct[conn_name]

        # Set Network Device for Connection
        self._dev = [
            dev
            for dev in NetworkManager.NetworkManager.GetDevices()
            if dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED and dev.Managed
            and dev.Ip4Config.Addresses == self._conn.GetSettings()['ipv4']['addresses']
        ][0]

    @property
    def conn_activated(self):
        conn_name = self._conn_name
        return any(
            conn.Id == conn_name and conn.State == NetworkManager.NM_ACTIVE_CONNECTION_STATE_ACTIVATED
            for conn in NetworkManager.NetworkManager.ActiveConnections
        )

    def connect(self):
        if self.conn_activated:
            return True

        while True:
            # Try Connection Activation
            conn = NetworkManager.NetworkManager.ActivateConnection(self._conn, self._dev, "/")
            try:
                # Check Connection Status, if it's still activating wait 1 second
                while conn.State == NetworkManager.NM_ACTIVE_CONNECTION_STATE_ACTIVATING:
                    time.sleep(1)
                else:
                    time.sleep(1)
                    return self.conn_activated
            except NetworkManager.ObjectVanished:
                return False

    def disconnect(self):
        conn_name = self._conn_name
        for conn in NetworkManager.NetworkManager.ActiveConnections:
            if conn.Id == conn_name and conn.State == NetworkManager.NM_ACTIVE_CONNECTION_STATE_ACTIVATED:
                NetworkManager.NetworkManager.DeactivateConnection(conn)
                return True

        return False


class NetMngVPNConn(NetMngConn):
    def __init__(self, conn_name, vpn_name):
        super().__init__(conn_name)

        # Set VPN Connection name
        self._conn_name = vpn_name

        # Set VPN Connection
        vpn = self._conn_dct[vpn_name]

        if vpn.GetSettings()['connection']['type'] == 'vpn':
            self._conn = vpn
        else:
            print("El nombre de la VPN no es válido", file=sys.stderr)
            sys.exit(1)
