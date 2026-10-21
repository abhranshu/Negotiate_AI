"""Print reverse dependencies for suspicious packages (sanity check)."""
import re
from importlib import metadata


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


dists = {norm(d.metadata["Name"]): d for d in metadata.distributions()
         if d.metadata["Name"]}

targets = ["pyperclip", "beartype", "uncalled-for", "docstring-parser",
           "watchdog", "cachetools", "whisper", "keyring", "aiofile",
           "code-review-graph", "fastmcp", "datasets", "spacy"]


def req_names(dist) -> set[str]:
    out = set()
    for req in dist.requires or []:
        r = req.split(";")[0].split("[")[0]
        r = r.split("=")[0].split(">")[0].split("<")[0].split("~")[0]
        r = r.split("!")[0].split(" ")[0].strip()
        if r:
            out.add(norm(r))
    return out


for t in targets:
    if t not in dists:
        print(f"{t}: NOT INSTALLED")
        continue
    requirers = sorted(o for o, d in dists.items() if o != t and t in req_names(d))
    print(f"{t}=={dists[t].version}")
    print(f"   requires: {sorted(req_names(dists[t]))}")
    print(f"   required by: {requirers}")

print("\nwhisper file:", dists["whisper"].locate_file("") if "whisper" in dists else "n/a")
