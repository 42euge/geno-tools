// Strict YAML-subset parser/serializer for geno manifests and SKILL.md frontmatter.
//
// Supported grammar:
//   - top-level "key: scalar" entries
//   - block scalars (">" / "|" with optional "-" chomp)
//   - lists of scalars ("- item")
//   - one level of nested maps, whose values may be scalars, block scalars, or lists
//   - inline flow lists of scalars ("[a, b]", "[]")
//
// Anything outside that grammar is a hard error: silently misparsing a manifest
// (the old parseYamlFast behavior) is worse than rejecting it with a line number.

export class YamlError extends Error {
  constructor(message, line) {
    super(line ? `${message} (line ${line})` : message);
    this.name = 'YamlError';
    this.line = line;
  }
}

function indentOf(line) {
  if (line[0] === '\t') throw new YamlError('Tabs are not allowed for indentation');
  return line.match(/^ */)[0].length;
}

function stripComment(line) {
  let inSingle = false;
  let inDouble = false;
  for (let j = 0; j < line.length; j++) {
    const c = line[j];
    if (c === "'" && !inDouble) inSingle = !inSingle;
    else if (c === '"' && !inSingle) inDouble = !inDouble;
    else if (c === '#' && !inSingle && !inDouble && (j === 0 || line[j - 1] === ' ')) {
      return line.slice(0, j);
    }
  }
  return line;
}

export function parseYaml(content) {
  const lines = content.split('\n');
  let i = 0;

  function unquote(v, lineNo) {
    if (v.length >= 2 &&
        ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'")))) {
      return v.slice(1, -1);
    }
    if (v.startsWith('"') || v.startsWith("'")) {
      throw new YamlError('Unterminated quoted string', lineNo);
    }
    if (v === 'true') return true;
    if (v === 'false') return false;
    if (v === 'null' || v === '~') return null;
    return v;
  }

  function parseScalar(raw, lineNo) {
    const v = raw.trim();
    if (/^[&*!]/.test(v)) {
      throw new YamlError(`Unsupported YAML feature "${v[0]}"`, lineNo);
    }
    if (v.startsWith('{')) throw new YamlError('Flow mappings are not supported', lineNo);
    if (v.startsWith('[')) {
      if (!v.endsWith(']')) throw new YamlError('Unterminated flow list', lineNo);
      const inner = v.slice(1, -1).trim();
      if (!inner) return [];
      return inner.split(',').map((s) => unquote(s.trim(), lineNo));
    }
    return unquote(v, lineNo);
  }

  function peekNextContent() {
    let j = i;
    while (j < lines.length) {
      const line = stripComment(lines[j]).trimEnd();
      if (line.trim()) return { indent: indentOf(line), text: line.trim(), index: j };
      j++;
    }
    return null;
  }

  function collectBlockScalar(style, parentIndent) {
    const fold = style[0] === '>';
    const chomp = style.includes('-');
    const buf = [];
    let blockIndent = null;
    while (i < lines.length) {
      const raw = lines[i];
      if (!raw.trim()) { buf.push(''); i++; continue; }
      const ind = indentOf(raw);
      if (ind <= parentIndent) break;
      if (blockIndent === null) blockIndent = ind;
      buf.push(raw.slice(Math.min(blockIndent, ind)));
      i++;
    }
    while (buf.length && buf[buf.length - 1] === '') buf.pop();
    let text = fold
      ? buf.map((l) => l.trim()).join(' ').replace(/ {2,}/g, ' ').trim()
      : buf.join('\n');
    if (!chomp && text) text += '\n';
    return text;
  }

  function parseList(parentIndent) {
    const arr = [];
    while (i < lines.length) {
      const line = stripComment(lines[i]).trimEnd();
      if (!line.trim()) { i++; continue; }
      const ind = indentOf(line);
      if (ind <= parentIndent) break;
      const t = line.trim();
      if (!t.startsWith('- ') && t !== '-') break;
      const item = t === '-' ? '' : t.slice(2).trim();
      if (item.endsWith(':') || /:\s/.test(item.replace(/(["']).*?\1/g, ''))) {
        throw new YamlError('Lists of mappings are not supported', i + 1);
      }
      arr.push(parseScalar(item, i + 1));
      i++;
    }
    return arr;
  }

  function parseMapping(minIndent, depth) {
    const obj = {};
    let mapIndent = null;
    while (i < lines.length) {
      const line = stripComment(lines[i]).trimEnd();
      if (!line.trim()) { i++; continue; }
      const trimmed = line.trim();
      if (trimmed === '---' || trimmed === '...') {
        if (depth === 0 && Object.keys(obj).length === 0) { i++; continue; }
        break;
      }
      const ind = indentOf(line);
      if (ind < minIndent) break;
      if (mapIndent === null) mapIndent = ind;
      if (ind > mapIndent) throw new YamlError('Unexpected indentation', i + 1);
      if (ind < mapIndent) break;

      const m = trimmed.match(/^([A-Za-z0-9_.-]+):(.*)$/);
      if (!m) throw new YamlError(`Expected "key: value", got "${trimmed}"`, i + 1);
      const key = m[1];
      const val = m[2].trim();
      const lineNo = i + 1;
      i++;

      if (val === '') {
        const next = peekNextContent();
        if (!next || next.indent <= mapIndent) {
          obj[key] = null;
        } else if (next.text.startsWith('- ') || next.text === '-') {
          obj[key] = parseList(mapIndent);
        } else {
          if (depth >= 1) {
            throw new YamlError(`Nesting too deep at "${key}" — geno YAML supports one level of nested maps`, lineNo);
          }
          obj[key] = parseMapping(mapIndent + 1, depth + 1);
        }
      } else if (/^[>|][+-]?$/.test(val)) {
        obj[key] = collectBlockScalar(val, mapIndent);
      } else {
        obj[key] = parseScalar(val, lineNo);
      }
    }
    return obj;
  }

  return parseMapping(0, 0);
}

function quoteIfNeeded(v) {
  if (typeof v !== 'string') return String(v);
  if (v === '' || /[:#"']/.test(v) || /^\s|\s$/.test(v) || /^(true|false|null|~|-)$/.test(v) || /^[\[{&*!>|]/.test(v)) {
    return `"${v.replace(/"/g, '\\"')}"`;
  }
  return v;
}

export function serializeYaml(obj) {
  let out = '';
  let first = true;
  for (const [key, value] of Object.entries(obj)) {
    if (value === null || value === undefined) continue;
    const isBlock = Array.isArray(value) || typeof value === 'object';
    if (!first && isBlock) out += '\n';
    first = false;
    if (Array.isArray(value)) {
      if (value.length === 0) { out += `${key}: []\n`; continue; }
      out += `${key}:\n`;
      for (const v of value) out += `  - ${quoteIfNeeded(v)}\n`;
    } else if (typeof value === 'object') {
      const entries = Object.entries(value).filter(([, v]) => v !== null && v !== undefined);
      if (entries.length === 0) continue;
      out += `${key}:\n`;
      for (const [k2, v2] of entries) {
        if (Array.isArray(v2)) {
          if (v2.length === 0) { out += `  ${k2}: []\n`; continue; }
          out += `  ${k2}:\n`;
          for (const v of v2) out += `    - ${quoteIfNeeded(v)}\n`;
        } else {
          out += `  ${k2}: ${quoteIfNeeded(v2)}\n`;
        }
      }
    } else {
      out += `${key}: ${quoteIfNeeded(value)}\n`;
    }
  }
  return out;
}

// Extracts and parses the leading "---" frontmatter block of a markdown file.
// Returns null when the file has no frontmatter.
export function parseFrontmatter(content) {
  if (!content.startsWith('---')) return null;
  const end = content.indexOf('\n---', 3);
  if (end === -1) return null;
  return parseYaml(content.slice(3, end));
}
