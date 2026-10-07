import { defineConfig } from 'wxt';

// WXT loads .env into process.env before it calls this function.
export default defineConfig({
  manifest: () => ({
    name: 'DoDAO Highlighter',
    description: 'Highlight and comment on docs.dodao.io',
    permissions: ['identity', 'storage', 'alarms'],
    host_permissions: ['https://docs.dodao.io/*', `${process.env.WXT_API_URL}/*`],
    oauth2: {
      client_id: process.env.WXT_GOOGLE_CLIENT_ID!,
      scopes: ['openid', 'email'],
    },
    // A fixed key gives the extension a fixed ID, which the Google client ID is tied to.
    ...(process.env.WXT_MANIFEST_KEY ? { key: process.env.WXT_MANIFEST_KEY } : {}),
  }),
});
