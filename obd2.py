import serialcom
import eml327

class Obd2Protocol(object):
    def establish_connection(self, port=None, baud_rate=None, protocol=None, timeout=0.1):
        available_ports = port or serialcom.serial_ports()
        if available_ports is None:
            raise ConnectionError("No available port(s)")

        for port in available_ports:
            self.connection = eml327.EML327Connection(port, baud_rate, timeout)

            try:
                self.connection.connect()

                print ("Successfully connected to port '%s'" % port)
                return
            except ConnectionError:
                raise

        self.connection = None

        raise ConnectionError("Failed to establish connection on all available port(s)")

    def close_connection(self):
        if self.connection is None:
            return

        try:
            self.connection.close()
        except:
            raise ConnectionError("Failed to close connection")