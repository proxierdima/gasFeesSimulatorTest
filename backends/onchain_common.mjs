import { readFileSync } from "node:fs";
import path from "node:path";
import { createClient } from "genlayer-js";
import { testnetBradbury, testnetAsimov } from "genlayer-js/chains";
import { privateKeyToAccount } from "viem/accounts";

export function parseJsonArray(text, label = "args") {
  let value;
  try {
    value = JSON.parse(text ?? "[]");
  } catch (error) {
    throw new Error(`Invalid JSON for ${label}: ${error.message}`);
  }
  if (!Array.isArray(value)) {
    throw new Error(`${label} must be a JSON array`);
  }
  return value;
}

export function requirePrivateKey() {
  const pk = (process.env.HARNESS_PRIVATE_KEY || "").trim();
  if (!pk) {
    throw new Error("HARNESS_PRIVATE_KEY is required for on-chain submission");
  }
  return pk.startsWith("0x") ? pk : `0x${pk}`;
}

export function resolveChain(rpcUrl = "") {
  const lowered = String(rpcUrl).toLowerCase();
  if (lowered.includes("asimov") || lowered.includes("studio.genlayer.com")) {
    return testnetAsimov;
  }
  return testnetBradbury;
}

export function createSignerClient(rpcUrl = "") {
  const chain = resolveChain(rpcUrl);
  const account = privateKeyToAccount(requirePrivateKey());
  const client = createClient({ chain, account });
  return { client, account, chain };
}

export function readContractCode(contractFile) {
  const filePath = path.resolve(process.cwd(), contractFile);
  return new Uint8Array(readFileSync(filePath));
}

export async function maybeInitConsensus(client) {
  if (typeof client.initializeConsensusSmartContract === "function") {
    await client.initializeConsensusSmartContract();
  }
}

export function buildGasOverrides(gaslimit) {
  const raw = String(gaslimit ?? "").trim();
  if (!raw) return {};
  const parsed = BigInt(raw);
  return {
    gas: parsed,
    gasLimit: parsed,
    gaslimit: parsed,
  };
}

export function extractGaslimit(tx) {
  if (!tx || typeof tx !== "object") return null;
  const candidate =
    tx.gaslimit ??
    tx.gasLimit ??
    tx.gas ??
    tx.transaction?.gaslimit ??
    tx.transaction?.gasLimit ??
    tx.transaction?.gas ??
    null;
  return candidate === null || candidate === undefined ? null : candidate;
}

export function normalizeScalar(value) {
  if (typeof value === "bigint") return value.toString();
  if (Array.isArray(value)) return value.map(normalizeScalar);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([k, v]) => [k, normalizeScalar(v)])
    );
  }
  return value;
}

export async function waitForVisibleTransaction(client, hash, retries = 25, intervalMs = 1000) {
  let lastError = null;
  for (let attempt = 1; attempt <= retries; attempt += 1) {
    try {
      const tx = await client.getTransaction({ hash });
      if (tx) return tx;
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  if (lastError) throw lastError;
  throw new Error(`Transaction ${hash} did not become visible after ${retries} attempts`);
}

async function rpcJson(rpcUrl, method, params) {
  const res = await fetch(rpcUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      method,
      params,
      id: 1,
    }),
  });

  const data = await res.json();
  if (data.error) {
    throw new Error(`RPC error for ${method}: ${JSON.stringify(data.error)}`);
  }
  return data.result;
}

export async function getRawTransactionByHash(rpcUrl, hash) {
  try {
    return await rpcJson(rpcUrl, "eth_getTransactionByHash", [hash]);
  } catch {
    return null;
  }
}

export async function ensureGasApplied({ tx, rpcUrl, txHash, requestedGas }) {
  const requested = BigInt(requestedGas);

  let onchain = extractGaslimit(tx);
  let rawTx = null;

  if (onchain === null && rpcUrl && txHash) {
    rawTx = await getRawTransactionByHash(rpcUrl, txHash);
    onchain = extractGaslimit(rawTx);
  }

  if (onchain === null) {
    return {
      appliedGas: null,
      rawTx,
      gasVerified: false,
      gasWarning:
        "RPC did not expose gas/gaslimit for this transaction via getTransaction() or eth_getTransactionByHash()",
    };
  }

  const actual = BigInt(onchain);
  if (actual !== requested) {
    throw new Error(
      `Gas override mismatch: requested ${requested.toString()}, on-chain ${actual.toString()}`
    );
  }

  return {
    appliedGas: actual,
    rawTx,
    gasVerified: true,
    gasWarning: null,
  };
}

export function successPayload(base) {
  return JSON.stringify(normalizeScalar(base));
}
