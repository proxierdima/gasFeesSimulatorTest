#!/usr/bin/env node
import { parseArgs } from "node:util";
import {
  buildGasOverrides,
  createSignerClient,
  ensureGasApplied,
  normalizeScalar,
  parseJsonArray,
  successPayload,
  waitForVisibleTransaction,
} from "./onchain_common.mjs";

const { values } = parseArgs({
  options: {
    rpc: { type: "string" },
    contract: { type: "string" },
    fn: { type: "string" },
    args: { type: "string", default: "[]" },
    gaslimit: { type: "string" },
  },
  allowPositionals: false,
});

if (!values.rpc || !values.contract || !values.fn || !values.gaslimit) {
  throw new Error("--rpc, --contract, --fn, and --gaslimit are required");
}

const fnArgs = parseJsonArray(values.args, "function args");
const requestedGas = BigInt(values.gaslimit);
const { client, chain } = createSignerClient(values.rpc);

const txHash = await client.writeContract({
  address: values.contract,
  functionName: values.fn,
  args: fnArgs,
  value: 0n,
  ...buildGasOverrides(values.gaslimit),
});

const tx = await waitForVisibleTransaction(client, txHash);
const gasCheck = await ensureGasApplied({
  tx,
  rpcUrl: values.rpc,
  txHash,
  requestedGas,
});

process.stdout.write(
  successPayload({
    tx_hash: txHash,
    contract_address: values.contract,
    gaslimit_requested: requestedGas,
    gaslimit_onchain: gasCheck.appliedGas,
    gaslimit_verified: gasCheck.gasVerified,
    gaslimit_warning: gasCheck.gasWarning,
    tx: normalizeScalar(tx),
    raw_tx: normalizeScalar(gasCheck.rawTx),
    chain: chain?.name || null,
    backend: "genlayer-js-onchain-write",
  })
);
