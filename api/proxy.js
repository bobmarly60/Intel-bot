export default async function handler(req, res) {
  const { url } = req.query;
  if (!url) return res.status(400).send("Missing url parameter");

  try {
    const response = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"
      }
    });
    
    const text = await response.text();
    res.status(response.status).send(text);
  } catch (e) {
    res.status(500).send(e.message);
  }
}
