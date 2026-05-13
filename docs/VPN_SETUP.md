# VPN Setup

Use this section if the monitored Windows computers should reach the server through your WireGuard VPN.

Current notes from the provided server details:

- VPN server endpoint: `<server-ip-or-host>:51820`
- Allowed subnet: `<vpn-subnet>`, for example `10.10.0.0/24`
- Persistent keepalive: `25`

Example client config template:

```ini
[Interface]
PrivateKey = user_PrivateKey
Address = 10.10.0.x/32

[Peer]
PublicKey = server_PublicKey
AllowedIPs = <vpn-subnet>
Endpoint = <server-ip-or-host>:51820
PersistentKeepalive = 25
```

Server-side note:

- WireGuard server config file mentioned in your notes:
  - `/etc/wireguard/wg0.conf`

Before relying on VPN for uploads:

1. Confirm the Windows computer can ping or SSH to the server address you intend to use in `config.json`.
2. Confirm port `22` is reachable over the VPN path.
3. If you want the agent to use a VPN-only address, replace `server.host` in `config.json` with that VPN IP or hostname.
