import { apiKey, user } from './store';

const API = import.meta.env.WXT_API_URL;

// The user types in an API key. The server says whether it knows the key, and
// whose it is. Only a key the server accepts is kept.
export async function signIn(key: string) {
  key = key.trim();
  if (!key) throw new Error('Enter an API key');
  const res = await fetch(`${API}/me`, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) throw new Error('The server does not know this API key');
  if (!res.ok) throw new Error(`Server answered ${res.status}`);
  const { name } = await res.json();
  await apiKey.setValue(key);
  await user.setValue(name);
}

export async function signOut() {
  await apiKey.setValue(null);
  await user.setValue(null);
}
