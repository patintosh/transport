// scripts/generate-index.js
const fs = require('fs');
const path = require('path');
const glob = require('glob');
const pdf = require('pdf-parse');
const { JSDOM } = require('jsdom');

const OUT = path.join(process.cwd(), 'index.json');

// Tes fichiers sont directement dans ~/Documents/transport
// Donc on scanne le dossier courant
const ROOT = process.cwd();

function safeIso(d) {
  if (!d) return null;
  const dt = new Date(d);
  return isNaN(dt) ? null : dt.toISOString();
}

async function processPdf(filePath) {
  const data = fs.readFileSync(filePath);
  const stat = fs.statSync(filePath);

  try {
    const info = await pdf(data);
    const text = (info.text || '').replace(/\s+/g, ' ').trim();

    const title =
      (info.info && (info.info.Title || info.info.title)) ||
      path.basename(filePath, '.pdf').replace(/[-_]/g, ' ');

    let date = null;
    if (info.info && info.info.ModDate) date = info.info.ModDate;
    if (!date && info.info && info.info.CreationDate) date = info.info.CreationDate;

    if (!date) {
      const m = filePath.match(/(\d{4})[^\d]?(\d{1,2})[^\d]?(\d{1,2})/);
      if (m) date = `${m[1]}-${m[2].padStart(2,'0')}-${m[3].padStart(2,'0')}`;
    }

    return {
      path: path.basename(filePath),
      title,
      date: safeIso(date),
      excerpt: text.slice(0, 400),
      type: 'pdf',
      size: stat.size
    };

  } catch (e) {
    return {
      path: path.basename(filePath),
      title: path.basename(filePath),
      date: null,
      excerpt: '',
      type: 'pdf',
      size: stat.size
    };
  }
}

async function processHtml(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  const stat = fs.statSync(filePath);
  const dom = new JSDOM(raw);
  const doc = dom.window.document;

  const title =
    (doc.querySelector('title') && doc.querySelector('title').textContent.trim()) ||
    (doc.querySelector('h1') && doc.querySelector('h1').textContent.trim()) ||
    path.basename(filePath);

  const text = doc.body ? doc.body.textContent.replace(/\s+/g, ' ').trim() : '';
  const head = text.slice(0, 1200);
  const tail = text.slice(-1200);

  const re = /P\.?S\.?\s*[:\-–]?\s*(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2,4})/i;
  const m = tail.match(re) || head.match(re);

  let date = null;
  if (m) {
    let day = parseInt(m[1],10);
    let month = parseInt(m[2],10) - 1;
    let year = parseInt(m[3],10);
    if (year < 100) year += (year <= 49 ? 2000 : 1900);
    date = new Date(year, month, day).toISOString();
  }

  return {
    path: path.basename(filePath),
    title,
    date,
    excerpt: text.slice(0, 400),
    type: 'html',
    size: stat.size
  };
}

async function main() {
  const items = [];

  // PDF dans transport/
  const pdfFiles = glob.sync(path.join(ROOT, '*.pdf'));
  for (const f of pdfFiles) {
    const it = await processPdf(f);
    items.push(it);
    console.log('PDF →', it.path);
  }

  // HTML dans transport/
  const htmlFiles = glob.sync(path.join(ROOT, '*.html'));
  for (const f of htmlFiles) {
    const it = await processHtml(f);
    items.push(it);
    console.log('HTML →', it.path);
  }

  fs.writeFileSync(OUT, JSON.stringify(items, null, 2), 'utf8');
  console.log('index.json écrit avec', items.length, 'documents');
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
