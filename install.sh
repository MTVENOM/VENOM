#!/data/data/com.termux/files/usr/bin/bash

pkg update -y
pkg install unzip termux-elf-cleaner -y

unzip -o SSL.zip

termux-elf-cleaner SSL.bin
cp SSL.bin $PREFIX/bin/venom
chmod +x $PREFIX/bin/venom

venom
