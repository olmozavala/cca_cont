#!/bin/bash
# Shared environment for scripts running on amate (local PostgreSQL, no SSH tunnel).

ROOT_PATH="/AIRE/home/olmozavala/CODE/cca_cont"

cd "$ROOT_PATH" || exit 1

export ROOT_PATH
export CCA_DB_SSH_TUNNEL=0
