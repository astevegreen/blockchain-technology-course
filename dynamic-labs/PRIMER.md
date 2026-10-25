# 🎓 Bitcoin Lab Environment: Student User Guide

Welcome to the Bitcoin Lab! This environment is a self-contained Linux workstation designed for experimenting with the Bitcoin protocol. You will access it through your web browser, which connects you to a terminal running inside the container.

This guide covers the essentials of navigating the Linux command line, reading files, managing your workspace with `zellij`, sharing files, and using the pre-installed tools. You type commands and read what they print; you never write or edit code.

---

## 1. 🐧 Linux CLI Basics

Your environment uses **Bash** (Bourne Again SHell). If you are new to Linux, the command line (CLI) is where you type text commands to perform actions instead of clicking icons.

### **Navigation & Files**

* **`pwd`** (Print Working Directory): Shows you where you are currently located in the file system.
```bash
user@container:~$ pwd
/home/user

```


* **`ls`** (List): Lists files and folders in the current directory.
* `ls -l`: Detailed list (sizes, permissions, dates).
* `ls -a`: Show hidden files (like `.bitcoin`).


* **`cd <directory>`** (Change Directory): Moves you into a folder.
* `cd scripts`: Go to the `scripts` folder.
* `cd ..`: Go back up one level.
* `cd ~`: Go back to your home folder (`/home/user`).


### **Reading Files**

* **`cat <file>`**: Dumps the entire content of a file to the screen. Good for short files.
* **`less <file>`**: Opens a file in a scrollable viewer. Press Space for the next page, `b` to go back, and `q` to exit.


* **`grep "<text>" <file>`**: Prints only the lines of a file that contain the text.
* *Example:* Find errors in the log: `grep "error" /home/user/.bitcoin/debug.log`



---

## 2. 🖥️ Zellij Primer (Window Management)

Because you are accessing this lab through a single browser tab, we use **zellij** (a terminal workspace) to give you tabs and split panes inside your terminal. This lets you run Bitcoin commands in one tab, read a file or script in another, and watch logs in a split pane.

### **What is zellij?**

Zellij manages multiple terminal views in one window. Press **`Ctrl + G`** to switch between zellij controls and locked shell input.

### **Cheatsheet**

| Action | Shortcut | Description |
| --- | --- | --- |
| **Toggle controls** | **`Ctrl + G`** | Switches between zellij controls and locked shell input. |
| **New pane** | **`Alt + n`** | Opens a new pane next to the current one. |
| **Navigate panes** | **`Alt + Arrow Keys`** | Moves focus between panes. |
| **Pane mode** | **`Ctrl + G`**, then **`p`** | Enters pane mode: **`r`** splits right, **`d`** splits down, **`x`** closes the pane. |
| **Tab mode** | **`Ctrl + G`**, then **`t`** | Enters tab mode: **`n`** creates a new tab, **`Left/Right`** switches tabs. |
| **Scroll mode** | **`Ctrl + G`**, then **`s`** | Enters scroll mode. Use arrows or Page Up/Down to read history. Press `Ctrl + G` to return to the shell. |

### **Example: Splitting and Merging**

1. **Split:** Press `Ctrl + G`, then `p`, then `r`. You now have a left and right pane.
2. **Work:** Run `tail -f ~/.bitcoin/debug.log` in the right pane to watch logs while you type commands in the left.
3. **Merge (Unsplit):** When finished with the logs, type `exit` in the right pane (or press `Ctrl + G`, then `p`, then `x`). The pane will disappear, and your left pane will expand to fill the screen again.

### **Scrolling**

Terminals don't scroll like web pages. To scroll up in zellij:

1. Press **`Ctrl + G`**, then **`s`** to enter scroll mode.
2. Use **Arrow Keys** or **Page Up/Down** to scroll through history.
3. Press **`Ctrl + G`** to return to the shell.

---

## 3. 📂 The `/share` Folder (Static Web Server)

The lab includes a built-in "drop box" to help you share information (like your Bitcoin wallet address or transaction IDs) with other students or the instructor without typing it out manually.

### **How it works**

* There is a special folder located at: **`/home/user/share`**
* Any file you put inside this folder is instantly accessible via a web browser on the lab network at port **8000**.

### **Example Usage**

1. **Save your address to a file:**
```bash
bitcoin-cli -datadir=/home/user/.bitcoin getnewaddress > ~/share/my_address.txt

```


2. **Access it:**
Other students can now run `curl` to see your address:
```bash
curl http://<YOUR_IP_ADDRESS>:8000/my_address.txt

```


*(You can find your IP address by running `ip a`)*.

Outside of the environment, you can access the static server
by changing `/student1/` in the URL to `/static-web-student1/`
(but change `1` to your student number).

---

## 4. 🛠️ Workstation Overview

Your environment comes pre-loaded with tools for querying your node, watching the network and reading the results.

### **Bitcoin Tools**

* **`bitcoin-cli`**: The primary tool for talking to your node.
* **Note:** You must specify the data directory flag (`-datadir`) just like the login message shows.
* *Check Chain Info:* `bitcoin-cli -datadir=/home/user/.bitcoin getblockchaininfo`
* *Check Peers:* `bitcoin-cli -datadir=/home/user/.bitcoin getpeerinfo`


* **`miner.py`**: A custom Python script in `~/scripts/` that lets you manually mine blocks. It is educational and shows you the hashing process.
* *Usage:* `python3 ~/scripts/miner.py`


* **`agent.py`**: A background agent that can generate random transaction traffic to make the network feel "alive".

### **Python Environment**

* A Python virtual environment is active by default, with **`bitcoinlib`** installed.
* It runs the ready-made scripts in `~/scripts/` and the instructor's demonstrations. You run and read these scripts; you never write them.

### **Network Tools**

* **`netcat` (nc)**: The "Swiss Army knife" of networking. Use it to send raw data to peers.
* **`curl`**: Used to fetch data from web servers (or the `/share` folder of other students).
* **`jq`**: A tool for making JSON output readable.
* *Example:* `bitcoin-cli -datadir=/home/user/.bitcoin getblockchaininfo | jq` makes the output colorful and easy to read.



### **Locations of Interest**

* **`~/.bitcoin/`**: The data directory. Contains the blockchain data, your wallet, and `debug.log`.
* **`~/scripts/`**: Contains the custom mining and agent scripts.
* **`~/share/`**: The public web folder.
