import obd2

if __name__ == '__main__':
    protocol = obd2.Obd2Protocol()

    protocol.establish_connection()
    protocol.close_connection()