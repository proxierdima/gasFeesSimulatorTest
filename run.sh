#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${1:-$HOME/glh_v4}"
PASSWORD="${PASSWORD:-12345678}"

export GLH_SUBMIT_DEPLOY_BACKEND_CMD='node backends/onchain_submit_deploy.mjs --rpc {rpc_url_sh} --contract-file {contract_file_sh} --constructor-args {args_json_sh} --gaslimit {gaslimit_sh}'
export GLH_SUBMIT_WRITE_BACKEND_CMD='node backends/onchain_submit_write.mjs --rpc {rpc_url_sh} --contract {contract_address_sh} --fn {function_name_sh} --args {args_json_sh} --gaslimit {gaslimit_sh}'

python3 main.py --project-root "$PROJECT_ROOT" --password "$PASSWORD"
