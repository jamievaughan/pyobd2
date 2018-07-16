import serial
import time
import re
import atcommands

class EML327Connection(object):
    __BAUD_RATES = [38400, 9600, 230400, 115200, 57600, 19200]
    __ELM_PROMPT = b'>'
    __RESPONSE_OK = 'OK'

    def __init__(self, port=None, baud_rate=None, timeout=10):
        self.__port = port
        self.__baud_rate = baud_rate
        self.__timeout = timeout

    def connect(self):
        try:
            self.__serial_port = serial.serial_for_url( 
                self.__port,
                parity = serial.PARITY_NONE,
                stopbits = 1,
                bytesize = 8,
                timeout = self.__timeout)

            self.__setup_connection()
        except serial.SerialException:
            raise ConnectionError("Failed to connect to serial port: %s" % self.__port)

    def close(self):
        if self.__serial_port is None:
            return

        self.send_at_command(atcommands.RESET, ok=False)
        self.__serial_port.close()

    def set_at_flag(self, flag, state, echo=False, ok=True, delay=None):
        command = flag + ('1' if state else '0')
        
        self.send_at_command(command, echo, ok, delay)

    def send_at_command(self, command, echo=False, ok=True, delay=None):
        response = self.send(b"%s%s" % (atcommands.PREFIX, command))
        if response is None:
            raise ConnectionError("No response from EML")

        if not ok:
            return response

        if echo:
            for line in response:
                if __RESPONSE_OK in line:
                    return response
        else:
            if len(response) == 1 and response[0] == __RESPONSE_OK:
                return response

        raise ConnectionError("Unexepcted response from EML: %s" % response)

    def send(self, data, delay=None):
        if self.__serial_port is None:
            return

        self.__write(data)

        if delay is None:
            time.sleep(delay)

        return self.__read_lines()

    def __setup_connection(self):
        baud_rate = self.__baud_rate or self.__auto_baud_rate()
        if baud_rate is None:
            raise ConnectionError("Failed to auto detect baud")

        try:
            self.send_at_command(atcommands.RESET, ok=False, delay=1)
            
            self.set_at_flag(atcommands.ECHO_FLAG, False, echo=True)
            self.set_at_flag(atcommands.HEADER_FLAG, True)
            self.set_at_flag(atcommands.LINEFEED_FLAG, False)
        except:
            raise ConnectionError("Failed to setup connection")

    def __auto_baud_rate(self):
        for baud_rate in self.__BAUD_RATES:
            try:
                self.__serial_port.baudrate = baud_rate

                self.__serial_port.flushInput()
                self.__serial_port.flushOutput()
                
                command = b"\x7F"

                # Write a nonsense command to get a prompt
                self.__write(command * 2);

                # If we're prompt then assume the correct baudrate
                response = self.__serial_port.read(1024)
                if response.endswith(self.__ELM_PROMPT):
                    return baud_rate
            except serial.SerialException:
                pass

    def __write(self, data):
        self.__serial_port.flushInput()
        self.__serial_port.write(b"%s\r\n" % data)
        self.__serial_port.flush()

    def __read(self):
        if self.__serial_port is None:
            return

        buffer = bytearray()

        while True:
            length = self.__serial_port.in_waiting or 1
            data = self.__serial_port.read(length)

            if data is None:
                break

            buffer.extend(data)

            if __ELM_PROMPT in data:
                break

        buffer = re.sub(b"\x00", b"", buffer)
        
        if buffer.endswith(self.ELM_PROMPT):
            buffer = buffer[:-1]

        decoded = buffer.decode()

        lines = [s.strip() for s in re.split("[\r\n]", string) if bool(s)]

        return lines