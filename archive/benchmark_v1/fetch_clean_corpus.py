import urllib.request
import json
import os
import pathlib

def fetch_clean_corpus():
    output_dir = pathlib.Path("benchmark/corpus/clean")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    headers = {"User-Agent": "SENTINEL-benchmark/1.0"}
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
        
    urls_to_try = [
        "https://api.github.com/repos/PatrickJS/awesome-cursorrules/contents/rules",
        "https://api.github.com/repos/PatrickJS/awesome-cursorrules/contents"
    ]
    
    items = []
    for url in urls_to_try:
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode("utf-8"))
                if isinstance(data, list):
                    items = data
                    break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            print(f"Failed to fetch {url}: {e}")
            return
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return

    if not items:
        print("Could not find rules directory or contents.")
        return

    fetched_count = 0
    failures = 0
    
    for item in items:
        if fetched_count >= 40:
            break
            
        if item.get("type") == "file" and (item.get("name", "").endswith(".cursorrules") or item.get("name", "").endswith(".mdc")):
            download_url = item.get("download_url")
            size = item.get("size", 0)
            
            if size > 50 * 1024:
                print(f"Skipping {item['name']} (too large: {size} bytes)")
                continue
                
            if not download_url:
                continue
                
            try:
                req = urllib.request.Request(download_url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    content = response.read()
                    
                base_name = item['name']
                if base_name.endswith(".mdc"):
                    base_name = base_name[:-4] + ".cursorrules"
                
                dest = output_dir / base_name
                # Avoid naming collisions
                if dest.exists():
                    dest = output_dir / f"{item['sha'][:8]}_{base_name}"
                    
                dest.write_bytes(content)
                fetched_count += 1
                print(f"Fetched {item['name']} ({fetched_count}/40)")
            except Exception as e:
                print(f"Failed to download {item['name']}: {e}")
                failures += 1
                
        elif item.get("type") == "dir" and "rules" in urls_to_try[0]:
            # If we hit the top-level repo, we might need to dig into directories
            # But the prompt says "List the directory, find .cursorrules files".
            # It's likely a flat dir or we are expected to download from that specific dir.
            # Actually awesome-cursorrules has subdirectories for each framework.
            # Let's handle subdirectories if we didn't find files directly.
            pass

    # Handle awesome-cursorrules structure: it's typically subdirectories containing .cursorrules
    if fetched_count < 40:
        for item in items:
            if fetched_count >= 40:
                break
            if item.get("type") == "dir":
                dir_url = item.get("url")
                if not dir_url:
                    continue
                req = urllib.request.Request(dir_url, headers=headers)
                try:
                    with urllib.request.urlopen(req) as response:
                        sub_items = json.loads(response.read().decode("utf-8"))
                        for sub_item in sub_items:
                            if fetched_count >= 40:
                                break
                            if sub_item.get("type") == "file" and sub_item.get("name", "").endswith(".cursorrules"):
                                download_url = sub_item.get("download_url")
                                size = sub_item.get("size", 0)
                                if size > 50 * 1024:
                                    continue
                                if not download_url:
                                    continue
                                try:
                                    req_dl = urllib.request.Request(download_url, headers=headers)
                                    with urllib.request.urlopen(req_dl) as response_dl:
                                        content = response_dl.read()
                                    dest = output_dir / f"{item['name']}_{sub_item['name']}"
                                    dest.write_bytes(content)
                                    fetched_count += 1
                                    print(f"Fetched {item['name']}/{sub_item['name']} ({fetched_count}/40)")
                                except Exception as e:
                                    print(f"Failed to download {item['name']}/{sub_item['name']}: {e}")
                                    failures += 1
                except Exception as e:
                    pass

    print(f"\nFetch complete. Successfully fetched: {fetched_count}. Failures: {failures}.")
    print(f"Total files in clean dir: {len(list(output_dir.glob('*.cursorrules')))}")

if __name__ == '__main__':
    fetch_clean_corpus()
