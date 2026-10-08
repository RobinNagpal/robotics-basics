import { GetParameterCommand, SSMClient } from '@aws-sdk/client-ssm';
import { createHash, timingSafeEqual } from 'node:crypto';

// The keys live in one SSM SecureString parameter, as JSON: {"robin": "<key>", ...}.
// The name is who the key belongs to, and it is written on every comment made with it.
// They are read again after five minutes, so a key added or removed there takes
// effect without a deploy.
const ssm = new SSMClient({});
const TTL = 5 * 60 * 1000;
let cache: { at: number; keys: Record<string, string> } | null = null;

async function load() {
  if (cache && Date.now() - cache.at < TTL) return cache.keys;
  const res = await ssm.send(
    new GetParameterCommand({ Name: process.env.API_KEYS_PARAM!, WithDecryption: true }),
  );
  cache = { at: Date.now(), keys: JSON.parse(res.Parameter?.Value ?? '{}') };
  return cache.keys;
}

// Hashing both sides first gives equal lengths, which timingSafeEqual needs.
const digest = (s: string) => createHash('sha256').update(s).digest();

export async function nameForKey(key: string): Promise<string | null> {
  if (!key) return null;
  const given = digest(key);
  for (const [name, k] of Object.entries(await load())) {
    if (timingSafeEqual(given, digest(k))) return name;
  }
  return null;
}
