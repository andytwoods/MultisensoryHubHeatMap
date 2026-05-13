import os
import re
import json
import hashlib

def scan_mdx_for_tracked_blocks(dir_path):
    """
    Scans MDX files in a directory for <TrackedBlock> tags.
    Returns a list of manifest entries.
    """
    manifest = []
    
    # Regex to match <TrackedBlock ...>...</TrackedBlock>
    # or <TrackedBlock ... />
    # We want to extract props: blockId, topic, concept, contentType, label
    block_re = re.compile(r'<TrackedBlock\s+([^>]*?)(?:/?>|>(.*?)</TrackedBlock>)', re.DOTALL)
    prop_re = re.compile(r'(\w+)=(?:{["\'](.*?)["\']}|["\'](.*?)["\']|{(.*?)})')

    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith((".mdx", ".md")):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, dir_path)
                page_path = "/" + rel_path.replace("\\", "/").replace(".mdx", "").replace(".md", "").replace("index", "")
                if page_path.endswith("/"):
                    page_path = page_path[:-1]
                if not page_path:
                    page_path = "/"

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                    matches = block_re.finditer(content)
                    for i, match in enumerate(matches):
                        props_str = match.group(1)
                        inner_content = match.group(2) or ""
                        
                        props = {}
                        for prop_match in prop_re.finditer(props_str):
                            name = prop_match.group(1)
                            val = prop_match.group(2) or prop_match.group(3) or prop_match.group(4)
                            props[name] = val
                        
                        block_id = props.get("blockId")
                        if not block_id:
                            continue
                            
                        # Generate hashes
                        content_hash = hashlib.sha256(inner_content.strip().encode()).hexdigest()[:16]
                        position_hash = hashlib.sha256(f"{page_path}:{i}".encode()).hexdigest()[:16]
                        
                        entry = {
                            "block_id": block_id,
                            "topic": props.get("topic", ""),
                            "concept": props.get("concept", ""),
                            "content_type": props.get("contentType", ""),
                            "label": props.get("label", ""),
                            "page_path": page_path,
                            "display_order": i,
                            "content_hash": content_hash,
                            "position_hash": position_hash
                        }
                        manifest.append(entry)
                        
    return manifest

def generate_manifest_json(dir_path, output_file):
    manifest = scan_mdx_for_tracked_blocks(dir_path)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest
