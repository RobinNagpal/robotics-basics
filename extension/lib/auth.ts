import { browser } from '#imports';
import { ALLOWED_EMAILS } from './allowed';
import { user } from './store';

export async function getToken(interactive: boolean): Promise<string | null> {
  try {
    const res = await browser.identity.getAuthToken({ interactive });
    return res.token ?? null;
  } catch {
    return null;
  }
}

export async function signIn() {
  const token = await getToken(true);
  if (!token) throw new Error('Google sign-in was cancelled');
  const res = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const info = await res.json();
  if (!info.email_verified || !ALLOWED_EMAILS.includes(info.email)) {
    await browser.identity.removeCachedAuthToken({ token });
    throw new Error(`${info.email} is not allowed to use this extension`);
  }
  await user.setValue(info.email);
}

export async function signOut() {
  await browser.identity.clearAllCachedAuthTokens();
  await user.setValue(null);
}
