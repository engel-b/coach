import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'

const base = process.env.DOCS_BASE ?? '/coach/'
if (!base.startsWith('/') || !base.endsWith('/')) {
  throw new Error(`DOCS_BASE must begin and end with /: ${base}`)
}

const output = new URL('../.vitepress/dist/', import.meta.url)
let checked = 0

function checkDirectory(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const file = join(directory, entry.name)
    if (entry.isDirectory()) {
      checkDirectory(file)
      continue
    }
    if (!entry.name.endsWith('.html')) continue

    const html = readFileSync(file, 'utf8')
    for (const [, url] of html.matchAll(/(?:href|src)="(\/[^"#]*)"/g)) {
      if (!url.startsWith(base)) {
        throw new Error(`${file}: ${url} is outside the site base ${base}`)
      }
    }
    checked += 1
  }
}

checkDirectory(output.pathname)
if (checked === 0) throw new Error('No HTML pages were built')
console.log(`Checked ${checked} pages for links under ${base}`)
