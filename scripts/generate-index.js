// scripts/generate-index.js
const fs = require('fs');
const path = require('path');
const glob = require('glob');
const pdf = require('pdf-parse');
const { JSDOM } = require('jsdom');

const OUT = path.join(process.cwd(), 'index.json');
const PDF_DIR = process.cwd();   // le dossier courant = transport/
const HTML_DIR = process.cwd();  // idem

function safeIso(d) { return d ? new Date(d).toISOString() : null; }

async function processPdf(filePath) {
  const data = fs.readFileSync(filePath);
  try {
    const info = await pdf(data);
    const text = (info.text || '').replace(/\s+/g, ' ').trim();
    const title = (info.info && (info.info.Title || info.info.title)) || path.basename(filePath, '.pdf').replace(/[-_]/g, ' ');
    // heuristique date: metadata ModDate or CreationDate
    let date = null;
    if (info.info && info.info.ModDate) date = info.info.ModDate;
    if (!date && info.info && info.info.CreationDate) date = info.info.CreationDate;
    // fallback filename
    if (!date) {
      const m = filePath.match(/(\d{4})[^\d]?(\d{1,2})[^\d]?(\d{1,2})/);
      if (m) date = `${m[1]}-${m[2].padStart(2,'0')}-${m[3].padStart(2,'0')}`;
    }
    return {
      path: path.relative(process.cwd(), filePath).replace(/\\/g, '/'),
      title: title,
      date: safeIso(date),
      excerpt: text.slice(0, 400),
      type: 'pdf',
      size: fs.statSync(filePath).size
    };
  } catch (e) {
    return {
      path: path.relative(process.cwd(), filePath).replace(/\\/g, '/'),
      title: path.basename(filePath),
      date: null,
      excerpt: '',
      type: 'pdf',
      size: fs.statSync(filePath).size
    };
  }
}

async function processHtml(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  const dom = new JSDOM(raw);
  const doc = dom.window.document;
  const title = (doc.querySelector('title') && doc.querySelector('title').textContent.trim()) ||
                (doc.querySelector('h1') && doc.querySelector('h1').textContent.trim()) ||
                path.basename(filePath);
  // chercher P.S. JJ/MM/AA dans début/fin
  const text = doc.body ? doc.body.textContent.replace(/\s+/g, ' ').trim() : '';
  const tail = text.slice(-1200);
  const head = text.slice(0, 1200);
  const re = /P\.?S\.?\s*[:\-–]?\s*(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2,4})/i;
  const m = tail.match(re) || head.match(re);
  let date = null;
  if (m) {
    let day = parseInt(m[1],10), month = parseInt(m[2],10)-1, year = parseInt(m[3],10);
    if (year < 100) year += (year <= 49 ? 2000 : 1900);
    date = new Date(year, month, day).toISOString();
  }
  return {
    path: path.relative(process.cwd(), filePath).replace(/\\/g, '/'),
    title,
    date,
    excerpt: text.slice(0, 400),
    type: 'html',
    size: fs.statSync(filePath).size
  };
}

async function main() {
  const items = [];
  // PDFs
  const pdfFiles = glob.sync(path.join(PDF_DIR, '**/*.pdf'));
  for (const f of pdfFiles) {
    const it = await processPdf(f);
    items.push(it);
    console.log('pdf ->', it.path);
  }
  // HTML pages
  const htmlFiles = glob.sync(path.join(HTML_DIR, '**/*.html'));
  for (const f of htmlFiles) {
    const it = await processHtml(f);
    items.push(it);
    console.log('html ->', it.path);
  }
  // normalize dates to ISO or null
  items.forEach(i => {
    if (i.date) {
      const d = new Date(i.date);
      i.date = isNaN(d) ? null : d.toISOString();
    } else i.date = null;
  });
  fs.writeFileSync(OUT, JSON.stringify(items, null, 2), 'utf8');
  console.log('index.json written with', items.length, 'items');
}

main().catch(e => { console.error(e); process.exit(1); });
