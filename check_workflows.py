import subprocess, json
r = subprocess.run(["gh", "api", "repos/ashim-khan-root/novel-ai/actions/workflows"], capture_output=True, text=True)
d = json.loads(r.stdout)
print("Total:", d.get("total_count"))
for w in d.get("workflows", []):
    print(f"  {w['id']}: {w['state']} -> {w['path']}")
