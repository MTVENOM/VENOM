VENOM TOOL

📥 Installation (Termux)

pkg update -y
pkg install git unzip -y

git clone https://github.com/MTVENOM/VENOM.git
cd VENOM

unzip SSL.zip
chmod +x SSL.bin
./SSL.bin

⚠️ Notes

- Works on 64-bit devices only
- No need to install Python
- If not working, install:

pkg install termux-elf-cleaner patchelf -y
