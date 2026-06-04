#!/usr/bin/env bash
# Run ON amate:  bash amate_diagnose_connectivity.sh
# With sudo:    sudo bash amate_diagnose_connectivity.sh
# Optional:     CLIENT_IP=144.174.11.43 sudo bash amate_diagnose_connectivity.sh

set -euo pipefail

CLIENT_IP="${CLIENT_IP:-144.174.11.43}"
HBA="/etc/postgresql/15/main/pg_hba.conf"
PG_CONF="/etc/postgresql/15/main/postgresql.conf"

echo "========== 1. Host / network =========="
hostname -f
hostname -I
ip -4 route show default 2>/dev/null || true

echo ""
echo "========== 2. Is PostgreSQL listening? =========="
ss -tlnp | grep 5432 || echo "NOT listening on 5432"
if [[ -r "${PG_CONF}" ]]; then
  echo "listen_addresses=$(grep -E '^listen_addresses' "${PG_CONF}" || echo '(default)')"
  echo "port=$(grep -E '^port' "${PG_CONF}" | head -1 || echo 5432)"
else
  echo "(cannot read ${PG_CONF})"
fi

echo ""
echo "========== 3. pg_hba (remote rules) =========="
if [[ -r "${HBA}" ]]; then
  grep -E '^[^#]' "${HBA}" | grep -v '^local' || true
  echo "--- rules mentioning ${CLIENT_IP} or 144.174 ---"
  grep -E '144\.174|contingencia|olmozavala' "${HBA}" || true
else
  echo "Run with sudo to read ${HBA}"
fi

echo ""
echo "========== 4. Host firewall =========="
echo "ufw:"
ufw status 2>/dev/null || echo "  (ufw not active or no permission)"
echo "firewalld:"
firewall-cmd --state 2>/dev/null || echo "  (not running)"
echo "iptables INPUT (first 20 lines):"
if [[ "${EUID}" -eq 0 ]]; then
  iptables -L INPUT -n -v --line-numbers 2>/dev/null | head -25
  echo "--- OUTPUT ---"
  iptables -L OUTPUT -n -v --line-numbers 2>/dev/null | head -15
  echo "--- nat PREROUTING ---"
  iptables -t nat -L -n -v 2>/dev/null | head -15
else
  echo "  (need sudo for iptables -L)"
fi
echo "nftables:"
nft list ruleset 2>/dev/null | head -30 || echo "  (none or no permission)"

echo ""
echo "========== 5. TCP test from amate to itself =========="
for addr in 127.0.0.1 132.248.8.152; do
  if timeout 2 bash -c "cat < /dev/null > /dev/tcp/${addr}/5432" 2>/dev/null; then
    echo "  ${addr}:5432 OPEN"
  else
    echo "  ${addr}:5432 FAIL"
  fi
done

echo ""
echo "========== 6. Recent PostgreSQL log errors =========="
if [[ "${EUID}" -eq 0 ]]; then
  LOG=$(find /var/log/postgresql -name '*.log' 2>/dev/null | head -1)
  if [[ -n "${LOG}" ]]; then
    echo "Log: ${LOG}"
    grep -iE 'fatal|error|144\.174|connection' "${LOG}" 2>/dev/null | tail -15 || echo "(no matching lines)"
  else
    journalctl -u postgresql@15-main -n 20 --no-pager 2>/dev/null || journalctl -u postgresql -n 20 --no-pager 2>/dev/null || true
  fi
else
  echo "(need sudo for logs)"
fi

echo ""
echo "========== 7. While you connect from laptop =========="
echo "On amate (needs sudo), run in another terminal:"
echo "  sudo tcpdump -ni any 'tcp port 5432 and host ${CLIENT_IP}'"
echo "Then from laptop:  nc -zv amate.atmosfera.unam.mx 5432"
echo "  - No packets seen  -> block BEFORE amate (network)"
echo "  - SYN seen, no reply -> amate firewall drops"
echo "  - SYN-ACK seen -> TCP OK; check pg_hba / auth"

echo ""
echo "========== 8. Live test with tcpdump (5s, needs sudo) =========="
if [[ "${EUID}" -eq 0 ]] && command -v tcpdump >/dev/null; then
  echo "Listening 5s for ${CLIENT_IP}:5432 (try nc from your PC now)..."
  timeout 5 tcpdump -ni any "tcp port 5432 and host ${CLIENT_IP}" -c 5 2>/dev/null || echo "(no packets captured)"
else
  echo "Skip (no sudo or no tcpdump)"
fi

echo ""
echo "Done."
