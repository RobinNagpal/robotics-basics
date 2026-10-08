import { defineConfig } from 'wxt';

export default defineConfig({
  manifest: () => ({
    name: 'DoDAO Highlighter',
    description: 'Highlight and comment on docs.dodao.io',
    permissions: ['storage', 'alarms'],
    // The server URL is typed into the popup, so the manifest cannot name it.
    // It lists every Lambda function URL instead, and the API run locally.
    host_permissions: ['https://docs.dodao.io/*', 'https://*.on.aws/*', 'http://localhost/*'],
  }),
});
