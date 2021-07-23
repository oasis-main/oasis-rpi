#/bin/bash -e

read -sp "Enter old password: " oldpwd
pwdline=`grep wpa_passphrase /etc/hostapd/hostapd.conf`

if [ "wpa_passphrase=$oldpwd" = "$pwdline" ]; then
    read -sp "Enter new password: " newpwd
    read -sp "Confirm new password: " newpwdconf

    if [ "$newpwd" = "$newpwdconf" ]; then
        sudo sed -i "s/$oldpwd/$newpwd/" /etc/hostapd/hostapd.conf
    fi
else
    echo "Incorrect password."
fi