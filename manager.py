from serial import Serial

import time

class Ports:
    def __init__(self, port_name, baud_rate):
        self.ser = Serial(port_name, baud_rate)

    def clear_buffer(self):
        self.ser.close()
        self.ser.open()
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        return True

    def send_command(self, command):
        response_lines = []
        self.ser.write((command + '\n').encode())
        time.sleep(1)

        while self.ser.in_waiting > 0:  # Пока есть данные в буфере
            print('working!')
            line = self.ser.readline().decode().strip()
            if line:
                response_lines.append(line)
        return response_lines

    def read(self):
        response_lines = []
        while self.ser.in_waiting > 0:  # Пока есть данные в буфере
            line = self.ser.readline().decode().strip()
            if line:
                response_lines.append(line)
        return response_lines

