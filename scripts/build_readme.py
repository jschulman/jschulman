# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "feedparser",
#   "pathlib",
# ]
# ///

import feedparser
import pathlib
import re
import datetime
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

root = pathlib.Path(__file__).parent.resolve()

def replace_chunk(content: str, marker: str, chunk: str, inline: bool = False) -> str:
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    if not inline:
        chunk = "\n{}\n".format(chunk)
    chunk = "<!-- {} starts -->{}<!-- {} ends -->".format(marker, chunk, marker)
    return r.sub(chunk, content)

def fetch_feed_entries(url: str, max_entries: int = 5) -> List[Dict[str, str]]:
    try:
        entries = feedparser.parse(url)["entries"]
        parsed_entries = []
        for entry in entries[:max_entries]:
            parsed_entry = {
                "title": entry.get("title", "No title"),
                "url": entry.get("link", "").split("#")[0],
            }
            parsed_entries.append(parsed_entry)
        return parsed_entries
    except Exception as e:
        logger.error(f"Error fetching feed from {url}: {str(e)}")
        return []

def read_file_content(file_path: pathlib.Path) -> str:
    try:
        return file_path.read_text()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return ""

def main():
    content = root / ".." / "content"
    readme = root / ".." / "README.md"

    file_paths = {
        "readme": readme,
        "bio": content / "bio.md",
        "links": content / "links.md",
        "details": content / "details.md",
        "github_stats": content / "github_stats.md",
        "social": content / "social.md",
    }

    file_contents = {name: read_file_content(path) for name, path in file_paths.items()}

    rewritten = file_contents["readme"]
    original_content = rewritten

    for section in ["bio", "links", "details", "github_stats", "social"]:
        rewritten = replace_chunk(rewritten, section, file_contents[section])

    # Fetch blog entries from jayschulman.com
    blog_entries = fetch_feed_entries("https://jayschulman.com/rss.xml")

    entries_md = "\n".join(
        ["* [{title}]({url})".format(**entry) for entry in blog_entries]
    )
    rewritten = replace_chunk(rewritten, "blog", entries_md)

    # Update build date
    builddate_md = "Generated on `" + datetime.datetime.now().strftime("%B %d, %Y") + "`"
    rewritten = replace_chunk(rewritten, "date", builddate_md)

    if rewritten != original_content:
        try:
            readme.write_text(rewritten)
            logger.info("README.md updated successfully")
        except Exception as e:
            logger.error(f"Error writing to README.md: {str(e)}")
    else:
        logger.info("No changes detected. README.md not updated.")

if __name__ == "__main__":
    main()
