import {
  DeleteObjectCommand,
  GetObjectCommand,
  ListObjectsV2Command,
  NoSuchKey,
  PutObjectCommand,
  S3Client,
  S3ServiceException,
} from '@aws-sdk/client-s3';
import type { Highlight } from './types';

// One JSON file per docs page, at feedback/<book>/<chapter>/<page>.json, holding
// every comment on that page in the order they were made. A page file is what a
// person or Claude reads to work through the feedback on one page.
const s3 = new S3Client({});
const BUCKET = process.env.FEEDBACK_BUCKET!;
const PREFIX = 'feedback/';

type PageRef = Pick<Highlight, 'book' | 'chapter' | 'page'>;

export const pageKeyOf = (p: PageRef) => `${PREFIX}${p.book}/${p.chapter}/${p.page}.json`;

async function read(key: string): Promise<{ items: Highlight[]; etag?: string }> {
  try {
    const res = await s3.send(new GetObjectCommand({ Bucket: BUCKET, Key: key }));
    return { items: JSON.parse(await res.Body!.transformToString()), etag: res.ETag };
  } catch (e) {
    if (e instanceof NoSuchKey) return { items: [] };
    throw e;
  }
}

// Read a page file, change it, and write it back only if nobody else wrote it in
// between. S3 refuses the write with 412 when the file changed, and then the
// whole read and change happen again on the new copy.
export async function updatePage(key: string, change: (items: Highlight[]) => Highlight[]) {
  for (let attempt = 0; attempt < 5; attempt++) {
    const { items, etag } = await read(key);
    const next = change(items).sort((a, b) => a.createdAt - b.createdAt);
    try {
      if (next.length === 0) {
        if (etag) await s3.send(new DeleteObjectCommand({ Bucket: BUCKET, Key: key, IfMatch: etag }));
      } else {
        await s3.send(
          new PutObjectCommand({
            Bucket: BUCKET,
            Key: key,
            Body: JSON.stringify(next, null, 2) + '\n',
            ContentType: 'application/json',
            ...(etag ? { IfMatch: etag } : { IfNoneMatch: '*' }),
          }),
        );
      }
      return;
    } catch (e) {
      const status = e instanceof S3ServiceException ? e.$metadata.httpStatusCode : 0;
      if (status !== 412 && status !== 409) throw e;
    }
  }
  throw new Error(`${key} kept changing; gave up after 5 tries`);
}

export async function readAll(): Promise<Highlight[]> {
  const keys: string[] = [];
  let token: string | undefined;
  do {
    const res = await s3.send(
      new ListObjectsV2Command({ Bucket: BUCKET, Prefix: PREFIX, ContinuationToken: token }),
    );
    keys.push(...(res.Contents ?? []).map((o) => o.Key!).filter((k) => k.endsWith('.json')));
    token = res.NextContinuationToken;
  } while (token);
  const pages = await Promise.all(keys.map(async (k) => (await read(k)).items));
  return pages.flat();
}
