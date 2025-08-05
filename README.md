# docker-honeypot

A Python-based, Docker-isolated honeypot prototype designed for understanding attacker behavior in a controlled environment. It spins up a fake shell interface inside a sandboxed Docker container with a decoy filesystem to trick and observe potential malicious activity.

> ⚠️ This is an **experimental project**. Some features may be incomplete or insecure. Use at your own risk and never run this on production systems.

---

## ⚠️ Disclaimer

- This project is intended **for educational and research purposes only**.
- Running honeypots can attract malicious activity. Ensure you understand the risks before deploying this on any internet-facing system.
- The developer (**me**) is **not responsible** for any misuse, data loss, or damage caused by running this software.
- Do **not expose this tool to the public internet** without proper security controls (e.g., firewalls, container hardening).

---

## 🔧 Features

- Docker-based isolation for safer command execution.
- Simulated filesystem with fake files like passwords, installers, and logs.
- Command logging with rotating logs.
- Threaded socket listener mimicking a remote shell.
- Useful for observing basic attacker behavior in a sandbox.

---

## 🚀 Setup Instructions

### Requirements

- Python 3.8+
- Docker (latest version)
- Linux environment (recommended)

### Installation

```bash
pip install .
