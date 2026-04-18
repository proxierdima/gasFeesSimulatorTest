#!/usr/bin/env node
import { parseArgs } from "node:util";
import {
  buildGasOverrides,
  createSignerClient,
  ensureGasApplied,
  maybeInitConsensus,
  normalizeScalar,
  parseJsonArray,
  readContractCode,
  successPayload,
  waitForVisibleTransaction,
} from "./onchain_common.mjs";

const { values } = parseArgs({
  options: {
    rpc: { type: "string" },
    "contract-file": { type: "string" },
    "constructor-args": { type: "string", default: "[]" },
    gaslimit: { type: "string" },
  },
  allowPositionals: false,
});

if (!values.rpc || !values["contract-file"] || !values.gaslimit) {
  throw new Error("--rpc, --contract-file, and --gaslimit are required");
}

const ctorArgs = parseJsonArray(values["constructor-args"], "constructor args");
const requestedGas = BigInt(values.gaslimit);
const { client, chain } = createSignerClient(values.rpc);
await maybeInitConsensus(client);

const txHash = await client.deployContract({
  code: readContractCode(values["contract-file"]),
  args: ctorArgs,
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
    contract_address:
      tx?.txDataDecoded?.contractAddress ||
      tx?.recipient ||
      null,
    gaslimit_requested: requestedGas,
    gaslimit_onchain: gasCheck.appliedGas,
    gaslimit_verified: gasCheck.gasVerified,
    gaslimit_warning: gasCheck.gasWarning,
    tx: normalizeScalar(tx),
    raw_tx: normalizeScalar(gasCheck.rawTx),
    chain: chain?.name || null,
    backend: "genlayer-js-onchain-deploy",
  })
);
