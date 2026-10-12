import {
  DeleteObjectCommand,
  GetObjectCommand,
  ListObjectsV2Command,
  NoSuchKey,
  PutObjectCommand,
  S3Client,
  S3ServiceException,
} from '@aws-sdk/client-s3';
import type { Batch, Highlight } from './types';

// One JSON file per docs page, at feedback/<book>/<chapter>/<page>.json, holding
// every comment on that page in the order they were made. A page file is what a
// person or Claude reads to work through the feedback on one page. One more file,
// batches.json, holds the record of each batch of work that was asked for. It
// sits outside the feedback/ prefix, so reading every page file never reads it.
const s3 = new S3Client({});
const BUCKET = process.env.FEEDBACK_BUCKET!;
const PREFIX = 'feedback/';
const BATCHES = 'batches.json';

// How many batch records to keep. The list is history a reader scrolls through,
// so it does not need to go back for ever, and one file that only grows would be
// read and written on every queue request. A batch the worker has not finished
// is never dropped, however old it is.
const KEEP_BATCHES = 100;

type PageRef = Pick<Highlight, 'book' | 'chapter' | 'page'>;

export const pageKeyOf = (p: PageRef) => `${PREFIX}${p.book}/${p.chapter}/${p.page}.json`;

async function read<T>(key: string): Promise<{ items: T[]; etag?: string }> {
  try {
    const res = await s3.send(new GetObjectCommand({ Bucket: BUCKET, Key: key }));
    return { items: JSON.parse(await res.Body!.transformToString()), etag: res.ETag };
  } catch (e) {
    if (e instanceof NoSuchKey) return { items: [] };
    throw e;
  }
}

// Read one JSON file, change it, and write it back only if nobody else wrote it
// in between. S3 refuses the write with 412 when the file changed, and then the
// whole read and change happen again on the new copy. What comes back is the list
// as it was written, which is how a caller learns a number the change worked out.
async function update<T>(key: string, change: (items: T[]) => T[]): Promise<T[]> {
  for (let attempt = 0; attempt < 5; attempt++) {
    const { items, etag } = await read<T>(key);
    const next = change(items);
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
      return next;
    } catch (e) {
      const status = e instanceof S3ServiceException ? e.$metadata.httpStatusCode : 0;
      if (status !== 412 && status !== 409) throw e;
    }
  }
  throw new Error(`${key} kept changing; gave up after 5 tries`);
}

// One page's comments, kept in the order they were made. What comes back is the
// page as it was written. A caller must read its answer from that rather than
// count anything inside `change`, because `change` runs again on a fresh copy
// whenever S3 refuses the write, and a count kept outside it would count twice.
export const updatePage = (key: string, change: (items: Highlight[]) => Highlight[]) =>
  update<Highlight>(key, (items) => change(items).sort((a, b) => a.createdAt - b.createdAt));

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
  const pages = await Promise.all(keys.map(async (k) => (await read<Highlight>(k)).items));
  return pages.flat();
}

// Every batch ever asked for, newest first, which is the order the extension
// lists them in.
export const readBatches = async () => (await read<Batch>(BATCHES)).items;

// Change the batch records. They are kept oldest first, so that working out the
// next number and finding the oldest unfinished batch both read one end of the
// list. The oldest finished records are dropped once there are more than
// KEEP_BATCHES of them.
export const updateBatches = (change: (items: Batch[]) => Batch[]) =>
  update<Batch>(BATCHES, (items) => {
    const next = change(items).sort((a, b) => a.number - b.number);
    const extra = next.length - KEEP_BATCHES;
    if (extra <= 0) return next;
    let dropped = 0;
    return next.filter((b) => {
      const drop = dropped < extra && (b.status === 'done' || b.status === 'failed');
      if (drop) dropped++;
      return !drop;
    });
  });
