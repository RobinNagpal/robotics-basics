import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  eslint: { ignoreDuringBuilds: true },

  // Exported as plain files rather than run as a server, so the whole site is
  // a directory that can be published to S3 and served from disk. Every
  // dynamic route already supplies generateStaticParams, which is what this
  // requires; the two route handlers are both GET and both force-static.
  //
  // The consequence to remember: the docs are read at BUILD time, so new or
  // edited Markdown reaches the site on the next build, not on the next
  // request. That is the trade for having no server to run.
  output: 'export',

  // `next start` serves /a/b for both a/b.html and a/b/index.html, but a plain
  // file server does not. Emitting directories with index.html in them is what
  // makes the export work unchanged behind any static server.
  trailingSlash: true,
};

export default nextConfig;
