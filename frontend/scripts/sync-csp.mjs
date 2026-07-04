/**
 * After `vite build`, SvelteKit (kit.csp mode: hash) injects a meta CSP tag with
 * sha256 hashes for its inline bootstrap script. This script:
 * 1. Reads that policy from build/index.html
 * 2. Appends frame-ancestors (only enforceable via HTTP header)
 * 3. Writes the full policy into nginx.conf
 * 4. Removes the meta tag so the document is governed by a single HTTP header
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const indexPath = resolve(root, 'build/index.html');
const nginxPath = resolve(root, 'nginx.conf');

const html = readFileSync(indexPath, 'utf8');
const match = html.match(/http-equiv="content-security-policy"\s+content="([^"]+)"/i);
if (!match) {
	throw new Error('CSP meta tag not found in build/index.html — is kit.csp configured?');
}

const directives = match[1].trim().replace(/;\s*$/, '');
const headerCsp = `${directives}; frame-ancestors 'none'`;

let nginx = readFileSync(nginxPath, 'utf8');
const cspLine = `add_header Content-Security-Policy "${headerCsp}" always;`;
if (!nginx.includes('add_header Content-Security-Policy ')) {
	throw new Error('nginx.conf is missing Content-Security-Policy add_header');
}
nginx = nginx.replace(/add_header Content-Security-Policy "[^"]*" always;/, cspLine);
writeFileSync(nginxPath, nginx);

const stripped = html.replace(/\n?\s*<meta http-equiv="content-security-policy"[^>]*>\n?/i, '\n');
writeFileSync(indexPath, stripped);

console.log('CSP synced to nginx.conf and meta tag removed from index.html');
