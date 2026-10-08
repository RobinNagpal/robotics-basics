// PM2's description of the worker. PM2 reads only JavaScript or JSON here, so
// this one file is not TypeScript; the worker itself is, and runs through tsx.
module.exports = {
  apps: [
    {
      name: 'feedback-worker',
      cwd: __dirname,
      script: 'index.ts',
      interpreter: 'node',
      node_args: ['--env-file=.env', '--import', 'tsx'],
      autorestart: true,
      // A crash loop should not run Claude over and over.
      restart_delay: 60_000,
      max_restarts: 10,
    },
  ],
};
