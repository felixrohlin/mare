// Lists every sentence the app can speak, per language, by reading the phrase table L from index.html.
// Names are never spoken, so no personal data ends up in the audio.
import fs from 'node:fs';
const html = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const m = html.match(/const L=(\{[\s\S]*?\});\n\/\/ level tables/);
if (!m) throw new Error('phrase table L not found in index.html');
const L = eval('(' + m[1] + ')');
const fill = (s, o) => s.replace(/\{(\w)\}/g, (_, k) => o[k]);
const out = {};
for (const [lang, t] of Object.entries(L)) {
  const set = new Set([t.hiS, t.who, t.popQ, t.countQ, t.quickQ, t.moreQ, t.addQ, t.subQ, t.together, t.again, t.star, t.up, t.isOne, ...t.praise]);
  for (let n = 1; n <= 10; n++) {
    set.add(String(n));
    for (const k of ['addA', 'subA']) set.add(fill(t[k], { a: n }));
    for (const k of ['addB', 'subB']) set.add(fill(t[k], { b: n }));
    if (n >= 2) { set.add(fill(t.isN, { n })); set.add(fill(t.popDone, { n })); }
  }
  for (let a = 2; a <= 10; a++) for (let b = 1; b < a; b++) set.add(fill(t.moreThan, { a, b }));
  out[lang] = [...set].map(s => s.trim()).filter(Boolean);
}
fs.writeFileSync(new URL('./phrases.json', import.meta.url), JSON.stringify(out, null, 1));
console.log(Object.fromEntries(Object.entries(out).map(([k, v]) => [k, v.length])));
