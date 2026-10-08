import { serve } from '@hono/node-server';
import { app } from './app';

// The same app as the Lambda, run on your own machine. It uses your own AWS
// credentials to reach the bucket and the key parameter named in .env.
serve({ fetch: app.fetch, port: Number(process.env.PORT ?? 8787) }, (i) =>
  console.log(`Feedback API on http://localhost:${i.port}`),
);
