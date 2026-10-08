import { defineConfig } from 'wxt';

// WXT loads .env into process.env before it calls this function.
export default defineConfig({
  manifest: () => ({
    name: 'DoDAO Highlighter',
    description: 'Highlight and comment on docs.dodao.io',
    permissions: ['storage', 'alarms'],
    // The API's address must be listed so the extension may call it.
    host_permissions: ['https://docs.dodao.io/*', `${process.env.WXT_API_URL}/*`],
  }),
});
