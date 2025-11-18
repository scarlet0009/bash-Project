#!/bin/bash
# Linux Login/Logout/Shutdown Email Notification Installer
# Author: ChatGPT

echo "============================================"
echo "  Linux Login/Logout Email Notification Tool"
echo "============================================"

# ------------------------------
# 1. Ask for Parent Email + Your Gmail + App Password
# ------------------------------
read -p "Enter your parent's Gmail: " abhishekaswal777@gmail.com    
read -p "Enter your Gmail address: "  rk95993931@gmail.com
read -p "Enter your Gmail App Password (NOT normal password): " bisu onsn nbmb fvyk


echo ""
echo "[+] Installing msmtp..."
sudo apt update -y
sudo apt install -y msmtp msmtp-mta

# ------------------------------
# 2. Create msmtp configuration
# ------------------------------

echo "[+] Configuring msmtp..."

cat > ~/.msmtprc <<EOF
defaults
auth           on
tls            on
tls_trust_file /etc/ssl/certs/ca-certificates.crt

account        gmail
host           smtp.gmail.com
port           587
from           $MY_GMAIL
user           $MY_GMAIL
password       $APP_PASS

account default : gmail
EOF

chmod 600 ~/.msmtprc

# ------------------------------
# 3. Create the email notification tool
# ------------------------------

echo "[+] Creating email notification tool..."

sudo bash -c "cat > /usr/local/bin/notify-parent.sh" <<EOF
#!/bin/bash

PARENT_EMAIL="$PARENT_EMAIL"
HOSTNAME=\$(hostname)
USER=\$(whoami)
TIME=\$(date)

echo -e \"Event: \$1\nUser: \$USER\nMachine: \$HOSTNAME\nTime: \$TIME\" | msmtp \"\$PARENT_EMAIL\"
EOF

sudo chmod +x /usr/local/bin/notify-parent.sh

# ------------------------------
# 4. Enable LOGIN Notification
# ------------------------------

echo "[+] Adding login notification..."

if [ -f ~/.bash_profile ]; then
    echo "/usr/local/bin/notify-parent.sh \"User LOGIN detected\"" >> ~/.bash_profile
else
    echo "/usr/local/bin/notify-parent.sh \"User LOGIN detected\"" >> ~/.bashrc
fi

# ------------------------------
# 5. Enable LOGOUT Notification
# ------------------------------

echo "[+] Adding logout notification..."

echo "/usr/local/bin/notify-parent.sh \"User LOGOUT detected\"" >> ~/.bash_logout

# ------------------------------
# 6. Enable SHUTDOWN Notification
# ------------------------------

echo "[+] Adding shutdown notification..."

sudo bash -c "cat > /usr/lib/systemd/system-shutdown/notify-shutdown.sh" <<EOF
#!/bin/bash
/usr/local/bin/notify-parent.sh "SYSTEM SHUTDOWN or REBOOT detected"
EOF

sudo chmod +x /usr/lib/systemd/system-shutdown/notify-shutdown.sh

# ------------------------------
# Finished
# ------------------------------

echo ""
echo "============================================"
echo " Setup Complete!"
echo " Notifications will be sent on:"
echo "   ✔ Login"
echo "   ✔ Logout"
echo "   ✔ Shutdown / Reboot"
echo "============================================"
echo "Test it by logging out or rebooting."
echo ""
