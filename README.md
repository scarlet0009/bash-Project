# SmartLogWatcher
A professional Bash-based Intrusion Detection & Auto-Blocking System for Linux.

## Features
- Real-time monitoring of SSH authentication logs  
- Detection of brute-force attempts  
- Automatic IP blocking via iptables/ufw  
- Auto-unblock mechanism  
- Daily reporting system  
- Extensible & modular design  
- Works on Ubuntu, Debian, CentOS, RHEL

---

# 📦 Installation Guide

## 1. Clone Repository
```bash
git clone https://github.com/yourusername/SmartLogWatcher.git
cd SmartLogWatcher
```

## 2. Install Scripts
```bash
sudo cp smartlogwatcher.sh /usr/local/bin/
sudo cp smartlogwatcher_block.sh /usr/local/bin/
sudo cp smartlogwatcher_report.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/smartlogwatcher*
```

## 3. Install Config
```bash
sudo cp smartlogwatcher.conf /etc/
```

## 4. Create Required Directories
```bash
sudo mkdir -p /var/log/smartlogwatcher /var/run/smartlogwatcher
```

## 5. Enable Systemd Service
```bash
sudo cp smartlogwatcher.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now smartlogwatcher
```

---

# Testing
To generate fake log activity:
```bash
echo "$(date) Failed password for invalid user test from 5.5.5.5 port 2222 ssh2" | sudo tee -a /var/log/auth.log
```

Check logs:
```bash
sudo tail -f /var/log/smartlogwatcher/suspicious.log
```

---

# License
MIT License
