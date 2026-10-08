import { apiKey, apiUrl, user } from './store';

// The extension may only call addresses listed in its manifest, so the server
// must be a Lambda function URL, or the API run on your own machine.
const ALLOWED = [/^https:\/\/[a-z0-9-]+\.lambda-url\.[a-z0-9-]+\.on\.aws$/, /^http:\/\/localhost(:\d+)?$/];

function serverUrl(url: string) {
  url = url.trim().replace(/\/+$/, '');
  if (!url) throw new Error('Enter the server URL');
  if (!ALLOWED.some((r) => r.test(url))) {
    throw new Error('The server URL must be a Lambda function URL, such as https://….lambda-url.us-east-1.on.aws');
  }
  return url;
}

// The user types in the server's URL and an API key. The server says whether it
// knows the key, and whose it is. Both are kept only if the server accepts the key.
export async function signIn(url: string, key: string) {
  url = serverUrl(url);
  key = key.trim();
  if (!key) throw new Error('Enter an API key');
  let res: Response;
  try {
    res = await fetch(`${url}/me`, { headers: { Authorization: `Bearer ${key}` } });
  } catch {
    throw new Error(`Could not reach ${url}`);
  }
  if (res.status === 401) throw new Error('The server does not know this API key');
  if (!res.ok) throw new Error(`Server answered ${res.status}`);
  const { name } = await res.json();
  await apiUrl.setValue(url);
  await apiKey.setValue(key);
  await user.setValue(name);
}

// The server URL is kept, so signing in again only needs the key.
export async function signOut() {
  await apiKey.setValue(null);
  await user.setValue(null);
}
