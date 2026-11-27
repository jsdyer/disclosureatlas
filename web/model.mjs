export function normalize(value) {
  return value.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replace(/[’']/g, '');
}

export function matches(record, {query = '', kind = '', region = ''}) {
  const words = normalize(query).trim().split(/\s+/).filter(Boolean);
  const haystack = normalize(record.search);
  return (!kind || kind === record.kind) && (!region || region === record.region)
    && words.every(word => haystack.includes(word));
}
