#!/data/data/com.termux/files/usr/bin/bash

pkg update -y
pkg install unzip -y

unzip -o SSL.zip
chmod +x SSL.bin
./SSL.bin
