import Link from 'next/link';

export default function NotFound() {
  return (
    <main className="not-found">
      <p className="eyebrow">404</p>
      <h1>This page is not in the library</h1>
      <p>The section may have been renamed or moved in the docs.</p>
      <Link href="/" className="button button-primary">
        Back to the library
      </Link>
    </main>
  );
}
