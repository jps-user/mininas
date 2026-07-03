# MiniNAS

> ⚠️ **Development Project** — This module is under active development and not yet ready for production use. Features may change, break, or be incomplete. Use at your own risk.

A lightweight Webmin module for Linux file sharing administration.

Built on top of Samba, Linux and Webmin – without replacing any of them.

## Features
- Share management with hybrid editor (structured fields + raw Samba parameters)
- User provisioning workflow (OS user + Samba user + directory + permissions in one step)
- Permission management with visual checkbox matrix
- HDD-neutral status checks (no unnecessary disk wake-ups)
- Atomic smb.conf writes with testparm validation and rollback

## Requirements
- Webmin
- Samba
- Debian/Ubuntu Linux

## Installation
```bash
cd /usr/share/webmin
git clone https://github.com/jps-user/mininas.git mininas
chmod +x mininas/*.cgi
```
Then restart Webmin and find MiniNAS under "Others" in the Webmin menu.

## Philosophy
See [PHILOSOPHY.md](PHILOSOPHY.md)
