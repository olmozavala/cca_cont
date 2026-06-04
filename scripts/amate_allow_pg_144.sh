#!/usr/bin/env bash
# Run ON amate with sudo:
#   sudo bash amate_allow_pg_144.sh
#
# Allows PostgreSQL access to database "contingencia" from 144.174.11.0/24
# (Florida State University / your current public range).

set -euo pipefail

CIDR="144.174.11.0/24"
DB_NAME="contingencia"
DB_USER="olmozavala"
HBA="/etc/postgresql/15/main/pg_hba.conf"
MARKER="# cca_cont: allow ${CIDR}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash $0" >&2
  exit 1
fi

if [[ ! -f "${HBA}" ]]; then
  echo "Missing ${HBA}" >&2
  exit 1
fi

if grep -qF "${MARKER}" "${HBA}"; then
  echo "pg_hba already has rule for ${CIDR}"
else
  cp -a "${HBA}" "${HBA}.bak.$(date +%Y%m%d%H%M%S)"
  {
    echo ""
    echo "${MARKER}"
    echo "host    ${DB_NAME}    ${DB_USER}    ${CIDR}    scram-sha-256"
  } >> "${HBA}"
  chown postgres:postgres "${HBA}"
  chmod 640 "${HBA}"
  echo "Added pg_hba entries for ${DB_USER}@${DB_NAME} from ${CIDR}"
fi

systemctl reload postgresql@15-main 2>/dev/null || systemctl reload postgresql
echo "PostgreSQL reloaded"

if command -v iptables >/dev/null 2>&1; then
  if ! iptables -C INPUT -p tcp -s "${CIDR}" --dport 5432 -j ACCEPT 2>/dev/null; then
    iptables -I INPUT 1 -p tcp -s "${CIDR}" --dport 5432 -j ACCEPT
    echo "iptables: allow ${CIDR} -> :5432"
  else
    echo "iptables rule already present"
  fi
else
  echo "iptables not found; if port 5432 stays blocked, ask UNAM IT to allow ${CIDR}"
fi

echo "Done. Test from your machine:"
echo "  psql -h amate.atmosfera.unam.mx -U ${DB_USER} -d ${DB_NAME}"
