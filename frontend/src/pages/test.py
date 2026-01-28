import subprocess; subprocess.run(["python3", "-c", open("MarketplacePage.tsx").read().replace("test", "替换")] + open("MarketplacePage.tsx", "w").write(""))
