import { serve } from '@hono/node-server';
import { Hono } from 'hono';
import postgres from 'postgres';
import { ALLOWED_EMAILS } from '../lib/allowed';
import type { Highlight } from '../lib/types';

const sql = postgres(process.env.DATABASE_URL!, { transform: postgres.camel, onnotice: () => {} });

await sql`
  create table if not exists highlights (
    id uuid primary key,
    book text not null,
    chapter text not null,
    page text not null,
    url text not null,
    text text not null,
    prefix text not null,
    suffix text not null,
    color text not null,
    note text not null,
    user_email text not null,
    created_at bigint not null,
    updated_at bigint not null
  )`;

const app = new Hono<{ Variables: { email: string } }>();

// The extension sends its Google access token. Google says whose it is.
app.use(async (c, next) => {
  const res = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
    headers: { Authorization: c.req.header('Authorization') ?? '' },
  });
  const info = res.ok ? await res.json() : {};
  if (!info.email_verified || !ALLOWED_EMAILS.includes(info.email)) return c.text('Unauthorized', 401);
  c.set('email', info.email);
  await next();
});

// One round trip: apply the browser's changes, then return everything.
// An upsert only wins over a row that was last changed earlier.
app.post('/sync', async (c) => {
  const { upserts = [], deletes = [] } = await c.req.json<{ upserts: Highlight[]; deletes: string[] }>();
  await sql.begin(async (tx) => {
    if (deletes.length) await tx`delete from highlights where id in ${tx(deletes)}`;
    for (const h of upserts) {
      await tx`
        insert into highlights ${tx({ ...h, userEmail: c.get('email') })}
        on conflict (id) do update set color = excluded.color, note = excluded.note, updated_at = excluded.updated_at
        where highlights.updated_at < excluded.updated_at`;
    }
  });
  const rows = await sql<Highlight[]>`select * from highlights`;
  return c.json(rows.map((r) => ({ ...r, createdAt: Number(r.createdAt), updatedAt: Number(r.updatedAt) })));
});

serve({ fetch: app.fetch, port: Number(process.env.PORT ?? 8787) }, (i) =>
  console.log(`Highlight server on http://localhost:${i.port}`),
);
