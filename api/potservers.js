// Same-site relay for the public Potservers API (https://potservers.net/api/v1).
// The Dinodex calls Potservers directly first; this only runs if a browser blocks that request.
// It relays read-only GET requests for creature, map and quest data. Nothing else is allowed.
const ALLOWED = /^\/(dinos|maps|quests)(\/[A-Za-z0-9_.-]{1,160})?$/;

module.exports = async (req, res) => {
  res.setHeader('x-dinodex-proxy', '1');
  if (req.method !== 'GET') {
    res.statusCode = 405;
    res.setHeader('Allow', 'GET');
    return res.end('Method not allowed');
  }
  const path = String((req.query && req.query.path) || '');
  if (!ALLOWED.test(path) || path.includes('..')) {
    res.statusCode = 400;
    return res.end('Unsupported path');
  }
  try {
    const upstream = await fetch('https://potservers.net/api/v1' + path, {
      headers: { 'User-Agent': 'potdinos.com (+https://potdinos.com)', Accept: 'application/json' },
    });
    const body = await upstream.text();
    res.statusCode = upstream.status;
    res.setHeader('Content-Type', upstream.headers.get('content-type') || 'application/json; charset=utf-8');
    if (upstream.ok) res.setHeader('Cache-Control', 'public, s-maxage=600, stale-while-revalidate=86400');
    else res.setHeader('Cache-Control', 'no-store');
    const retry = upstream.headers.get('retry-after');
    if (retry) res.setHeader('Retry-After', retry);
    return res.end(body);
  } catch (err) {
    res.statusCode = 502;
    res.setHeader('Cache-Control', 'no-store');
    return res.end(JSON.stringify({ error: 'upstream_unreachable' }));
  }
};
