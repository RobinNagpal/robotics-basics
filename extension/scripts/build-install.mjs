// Puts the install page and the zipped extension in .install/, ready to upload.
// Run `npm run zip` first. FEEDBACK_API_URL is the server URL the page shows.
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';

const { name, version } = JSON.parse(readFileSync('package.json', 'utf8'));
const server = process.env.FEEDBACK_API_URL?.replace(/\/+$/, '');
if (!server) throw new Error('Set FEEDBACK_API_URL to the Lambda function URL');

mkdirSync('.install', { recursive: true });
// One fixed name, so the page's download link never changes.
copyFileSync(`.output/${name}-${version}-chrome.zip`, '.install/dodao-highlighter.zip');
const html = readFileSync('install/index.html', 'utf8')
  .replaceAll('{{VERSION}}', version)
  .replaceAll('{{BUILT}}', new Date().toISOString().slice(0, 10))
  .replaceAll('{{SERVER_URL}}', server);
writeFileSync('.install/index.html', html);
console.log(`.install/ ready: version ${version}, server ${server}`);
