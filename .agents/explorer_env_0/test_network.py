import httpx
import json
import yaml
import os

def test_api_and_formats():
    results = {}
    
    # 1. Test Wikimedia Commons API query
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": "transistor",
        "gsrlimit": 3,
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata|user"
    }
    
    headers = {
        "User-Agent": "Harness9-Explorer/1.0 (test@example.com)"
    }
    
    try:
        with httpx.Client(timeout=10.0, headers=headers) as client:
            resp = client.get(url, params=params)
            results["wikimedia_status"] = resp.status_code
            if resp.status_code == 200:
                data = resp.json()
                pages = data.get("query", {}).get("pages", {})
                sample_assets = []
                for pid, pdata in pages.items():
                    title = pdata.get("title")
                    imginfo = pdata.get("imageinfo", [{}])[0]
                    file_url = imginfo.get("url")
                    meta = imginfo.get("extmetadata", {})
                    license_name = meta.get("LicenseShortName", {}).get("value", "Unknown")
                    artist = meta.get("Artist", {}).get("value", "Unknown")
                    sample_assets.append({
                        "title": title,
                        "url": file_url,
                        "license": license_name,
                        "author": artist
                    })
                results["sample_assets"] = sample_assets
    except Exception as e:
        results["wikimedia_error"] = str(e)
        
    # 2. Test YAML serialization
    sample_dossier = {
        "topic": "The History of the Transistor",
        "claims": [
            {
                "claim": "The point-contact transistor was invented at Bell Labs in December 1947.",
                "confidence": 0.98,
                "sources": ["https://en.wikipedia.org/wiki/Transistor"]
            }
        ]
    }
    yaml_str = yaml.dump(sample_dossier)
    results["yaml_support"] = len(yaml_str) > 0
    
    with open(r"g:\Finding-new-code\harness9\.agents\explorer_env_0\network_probe_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    test_api_and_formats()
