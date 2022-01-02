# rpi-ansible

Ansible playbooks for setting up Raspberry Pi's at my home for metrics collection,
compute experiments, alerting, home automation, robotics, computer vision and IoT.

Below is a simple grafana dashboard displays some metrics I'm collecting from different
pi hosts.

![grafana dashboard misty mountain](https://user-images.githubusercontent.com/965430/46509715-354fb380-c7f9-11e8-87a5-4e655da2026f.png)

### Prerequisite: setting up Raspberry Pi OS

**SD card and Raspberry Pi OS**

- Download Raspbian
- Download Etcher
- Load SD card to your computer
- Flash Raspbian to SD card with Etcher
- Load SD to Raspberry Pi

**Enable SSH and WiFi**

- Start Raspberry Pi by connecting it to power
- Log in with default username `pi` and password `raspberry`
- Run `sudo raspi-config`
- Go to `Interfacing Options` then `SSH` and then select `Yes` -> `Ok` -> `Finish`

- Run `sudo iwlist wlan0 scan | grep ESSID` to find a list of available WIFI SSIDs
- Run `wpa_passphrase "<your_wifi_ssid>"` and then type the wifi passphrase in stdin
- Copy the generated block which starts with `network={`
- Run `sudo vi /etc/wpa_supplicant/wpa_supplicant.conf`
- Paste the previously copied wifi config on the bottom
- Add `country=CA` (replace `CA` with your ISO country code)
- Use `:x` to save and quit vi
- Run `wpa_cli -i wlan0 reconfigure` to reconfigure the wifi interface
- Use `ifconfig wlan0` to verify if wifi has successfully connected

**Enable pubkey only access**

- Run `cat ~/.ssh/id_rsa.pub | ssh <USERNAME>@<IP-ADDRESS> 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys'`
- e.g. `cat ~/.ssh/raspbian/id_rsa.pub | ssh pi@192.168.2.7 'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys'`
- Run `sudo vi /etc/ssh/sshd_config`
- Change `#PasswordAuthentication yes` to `PasswordAuthentication no`
- Use `:x` to save and quit
- Run `sudo service ssh restart`

**Change hostname**

- Use `sudo vi /etc/hostname` to modify default hostname
- Also `sudo vi /etc/hosts` and change hostname for `127.0.1.1`
