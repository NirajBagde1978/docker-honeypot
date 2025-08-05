import logging
from logging.handlers import RotatingFileHandler
import socket
import docker
import tarfile
import io
import threading
import os

HOST ='0.0.0.0'
PORT=2222

class Logging:
    def __init__(self):
        self.format = logging.Formatter('%(asctime)s - %(message)s')
        self.setup_logs()

    def setup_logs(self):
        ip_logger = logging.getLogger('IPLog')
        ip_logger.setLevel(logging.INFO)
        if not ip_logger.hasHandlers():
            ip_handler = RotatingFileHandler('audits.log', maxBytes=1024, backupCount=5)
            ip_handler.setFormatter(self.format)
            ip_logger.addHandler(ip_handler)

        cmd_logger = logging.getLogger('AttackLog')
        cmd_logger.setLevel(logging.INFO)
        if not cmd_logger.hasHandlers():
            cmd_handler = RotatingFileHandler('cmd_audits.log', maxBytes=1024, backupCount=5)
            cmd_handler.setFormatter(self.format)
            cmd_logger.addHandler(cmd_handler)


class DockerSandbox:
    def __init__(self):
        self.client = docker.from_env()
        self.container = self._start_container()

    def _create_tar(self, filename, content):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w') as tar:
            tarinfo = tarfile.TarInfo(name=filename)
            encoded = content.encode()
            tarinfo.size = len(encoded)
            tar.addfile(tarinfo, io.BytesIO(encoded))
        data.seek(0)
        return data

    def _start_container(self):
        honeypot_script = """
                                import os

                                def create_fake_files():
                                    base_dir = "/fake_root"
                                    os.makedirs(base_dir + "/confidential", exist_ok=True)
                                    os.makedirs(base_dir + "/downloads", exist_ok=True)
                                    os.makedirs(base_dir + "/logs", exist_ok=True)

                                    with open(base_dir + "/confidential/passwords.txt", "w") as f:
                                        f.write("admin:123456\\nroot:toor\\n")

                                    with open(base_dir + "/downloads/fake_installer.exe", "w") as f:
                                        f.write("This is a fake installer.")

                                    with open(base_dir + "/logs/system.log", "w") as f:
                                        f.write("System started successfully.")

                                create_fake_files()
                            """

        container = self.client.containers.run(
            image="python:3.11-slim",
            command="sleep infinity",
            detach=True,
            tty=True
        )

        tar_stream = self._create_tar("honeypot.py", honeypot_script)
        container.put_archive(path="/", data=tar_stream)
        container.exec_run("python /honeypot.py")
        return container

    def exec_command(self, command):
        result = self.container.exec_run(command, demux=True)
        stdout, stderr = result.output
        output = b""
        if stdout:
            output += stdout
        if stderr:
            output += stderr
        if not output:
            output = b"\n"
        return output

def shell(channel, ip):
    Logging()
    ip_logger = logging.getLogger('IPLog')
    cmd_logger = logging.getLogger('AttackLog')

    ip_logger.info(f"Connection from {ip}")

    sandbox = DockerSandbox()
    channel.send(b"Tower$ ")

    command = b""
    cwd = "/" 

    while True:
        char = channel.recv(1)
        if not char:
            channel.close()
            break

        channel.send(char)
        command += char

        if char in [b'\r', b'\n']:
            command_str = command.strip().decode(errors='ignore')
            cmd_logger.info(f"{ip} - {command_str}")

            if command_str.lower() == "exit":
                channel.send(b"\nBye!\n")
                channel.close()
                break

            elif command_str.startswith("cd"):
                parts = command_str.split(maxsplit=1)
                if len(parts) == 1 or parts[1] in ("", "~"):
                    new_cwd = "/"  # Reset to root or your fake root
                else:
                    new_dir = parts[1].strip()
                    new_cwd = os.path.normpath(os.path.join(cwd, new_dir))

                # Test if directory exists inside container
                test_cmd = f"cd {new_cwd} && echo OK || echo FAIL"
                test_result = sandbox.exec_command(f"/bin/sh -c \"{test_cmd}\"").decode(errors='ignore').strip()

                if test_result == "OK":
                    cwd = new_cwd
                else:
                    channel.send(f"\nbash: cd: {parts[1]}: No such file or directory\n".encode())

                channel.send(b"Tower$ ")

            else:
                full_cmd = f"cd {cwd} && {command_str}"
                result = sandbox.exec_command(f"/bin/sh -c \"{full_cmd}\"")
                channel.send(b"\n" + result + b"\n")
                channel.send(b"Tower$ ")

            command = b""


def handle_client(client_socket, client_address):
    print(f"[+] New connection from {client_address[0]}")
    try:
        shell(client_socket, client_address[0])  # Your shell function
    except Exception as e:
        print(f"[!] Error with {client_address[0]}: {e}")
    finally:
        client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"[*] Honeypot listening on {HOST}:{PORT}...")
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            thread.start()
    except KeyboardInterrupt:
        print("\n[!] Shutting down honeypot.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()
