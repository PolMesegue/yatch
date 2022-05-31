#!/bin/bash
pass=$(gpg --gen-random --armor 1 14)
tor_pass=$(tor --hash-password $pass | grep -v warn)
echo -e "ControlPort 9051\nHashedControlPassword $tor_pass" | tee /etc/tor/torrc
service tor start
python3 main.py -h $pass $@