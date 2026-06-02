import httpx

from codec.tools.registry import register_tool


@register_tool("web_fetch", "Fetch a URL and return its content as markdown")
async def web_fetch(url: str, timeout: int = 30) -> str:
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "CodeC/1.0"})
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            text = resp.text

            if "text/html" in content_type or "text/plain" in content_type:
                import html
                text = html.unescape(text)
                import re
                text = re.sub(r"<[^>]+>", "", text)
                text = re.sub(r"\n{3,}", "\n\n", text)

            max_len = 10000
            if len(text) > max_len:
                text = text[:max_len] + f"\n... (truncated, {len(text)} total chars)"

            return text.strip() or "(empty response)"
    except httpx.TimeoutException:
        return f"Error: request timed out after {timeout}s"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} for {url}"
    except Exception as e:
        return f"Error fetching URL: {e}"


@register_tool("web_search", "Search the web for information. Returns top results with snippets.")
async def web_search(query: str, num_results: int = 5) -> str:
    try:
        import urllib.parse
        q = urllib.parse.quote(query)
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            url = f"https://html.duckduckgo.com/html/?q={q}"
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            text = resp.text

        import re
        results = []
        for m in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', text, re.DOTALL):
            link = m.group(1)
            title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            results.append(f"{title}\n  {link}")

        if not results:
            return "(no search results found)"

        output = "\n\n".join(results[:num_results])
        if len(results) > num_results:
            output += f"\n\n... ({len(results)} total results, showing {num_results})"
        return output
    except Exception as e:
        return f"Error searching web: {e}"
