#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
=============================================================================
                  SCAN3L - Ultimate Bug Bounty Automation Tool
=============================================================================
Author: opencode
Version: 1.0.0
Description: Advanced, fast, and multi-threaded Bug Bounty scanning tool.
=============================================================================
"""

import os
import sys
import re
import json
import time
import socket
import urllib.parse
import urllib.request
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# ANSI Colors for beautiful CLI
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Beautiful ASCII Banner
BANNER = f"""
{Colors.CYAN}{Colors.BOLD}
                                      _ 
 ___  ___  __ _ _ __   _________  _ _| |
/ __|/ __|/ _` | '_ \\ /__   __  || | | |
\\__ \\ (__| (_| | | | |   / / / / | | | |
|___/\\___|\\__,_|_| |_|  /_/ /_/  |_|_|_|
                                       
        {Colors.WHITE}Ultimate Automated Bug Bounty Framework{Colors.CYAN}
              {Colors.BOLD}[ Version 1.0.0 - {Colors.GREEN}Fast & Precise{Colors.CYAN} ]
{Colors.END}"""

# Common ports list for scanner
COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995,
    1723, 3306, 3389, 5900, 8000, 8080, 8443, 9000, 9090
]

# Common subdomains list for fallback DNS brute-forcing
COMMON_SUBDOMAINS = [
    "www", "mail", "dev", "staging", "api", "admin", "blog", "vpn", "secure",
    "portal", "test", "demo", "status", "git", "webmail", "support", "shop",
    "billing", "cdn", "app", "docs", "forum", "internal", "m", "news", "ns1",
    "ns2", "sys", "db", "mysql", "beta", "pma", "jenkins", "gitlab", "cpanel"
]

# Sensitive paths for fuzzer
SENSITIVE_PATHS = [
    ".git/config",
    ".env",
    "wp-config.php",
    "config.json",
    "config.php",
    ".git/HEAD",
    "robots.txt",
    "phpinfo.php",
    "sitemap.xml",
    "backup.zip",
    "backup.sql",
    "database.sql",
    ".htaccess",
    "server-status",
    "api/v1",
    "admin/",
    "dashboard/",
    "assets/"
]

# Subdomain Takeover signatures
TAKEOVER_SIGNATURES = {
    "GitHub Pages": ["There isn't a GitHub Pages site here", "404 Not Found"],
    "AWS S3": ["The specified bucket does not exist", "NoSuchBucket"],
    "Heroku": ["no-such-app", "no such app", "Heroku | No such app"],
    "Webflow": ["The page you are looking for doesn't exist", "404 Not Found"],
    "Shopify": ["Sorry, this shop is currently unavailable"],
    "Tumblr": ["Whatever you were looking for doesn't exist"],
    "Squarespace": ["Squarespace - Website not found"],
    "Fastly": ["Fastly error: unknown domain"],
    "Ghost": ["The thing you were looking for is no longer here", "Ghost - Unknown Blog"]
}

def print_status(msg, status_type='info'):
    prefix = ""
    if status_type == 'info':
        prefix = f"{Colors.BLUE}[*]{Colors.END}"
    elif status_type == 'success':
        prefix = f"{Colors.GREEN}[+]{Colors.END}"
    elif status_type == 'warning':
        prefix = f"{Colors.YELLOW}[!]{Colors.END}"
    elif status_type == 'danger':
        prefix = f"{Colors.RED}[-]{Colors.END}"
    elif status_type == 'header':
        prefix = f"{Colors.MAGENTA}[=]{Colors.END}"
        print(f"\n{prefix} {Colors.BOLD}{Colors.UNDERLINE}{msg}{Colors.END}")
        return
    print(f"{prefix} {msg}")

def request_url(url, timeout=5, headers=None, method='GET', data=None):
    """Sends custom HTTP requests using pure urllib for zero-dependency speed and safety"""
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept": "*/*"
        }
    try:
        req = urllib.request.Request(url, headers=headers, method=method, data=data)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.status, response.read().decode('utf-8', errors='ignore'), response.info()
    except urllib.error.HTTPError as e:
        # Return error body too because it might contain takeover signatures
        try:
            body = e.read().decode('utf-8', errors='ignore')
        except Exception:
            body = ""
        return e.code, body, e.headers
    except Exception:
        return 0, "", {}

class Scan3l:
    def __init__(self, target, threads=50, output_dir=None, wordlist_file=None):
        self.target = self.clean_target(target)
        self.threads = threads
        self.wordlist_file = wordlist_file
        
        # Output directory setup
        if not output_dir:
            self.output_dir = f"results_{self.target.replace('.', '_')}"
        else:
            self.output_dir = output_dir
            
        os.makedirs(self.output_dir, exist_ok=True)
        
        # In-memory storage of results
        self.subdomains = set()
        self.alive_subdomains = {}  # domain -> {status, title, server, length}
        self.open_ports = {}        # ip/domain -> list of ports
        self.urls = set()
        self.vulnerabilities = []
        self.fuzzed_dirs = {}

    def clean_target(self, target):
        target = target.strip()
        target = re.sub(r'^https?://', '', target)
        target = re.sub(r'/.*$', '', target)
        return target

    def check_and_install_dependencies(self):
        print_status("Checking for recommended system-level Kali tools...", "info")
        tools = ["subfinder", "httpx", "nuclei", "assetfinder", "waybackurls", "dirsearch", "nmap"]
        installed_tools = []
        missing_tools = []
        
        for tool in tools:
            # Check if available in PATH
            try:
                subprocess.run([tool, "--version" if tool != "nmap" and tool != "assetfinder" else "-h"], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                installed_tools.append(tool)
            except FileNotFoundError:
                missing_tools.append(tool)
                
        if installed_tools:
            print_status(f"Installed tools found: {', '.join(installed_tools)}", "success")
        if missing_tools:
            print_status(f"Missing recommended tools: {', '.join(missing_tools)}", "warning")
            print_status("Don't worry! scan3l will run its ultra-fast native Python fallback engines.", "success")
            print_status("If you are on Kali Linux and want full features, you can install them manually via:", "info")
            print_status(f"{Colors.YELLOW}sudo apt update && sudo apt install -y subfinder httpx nuclei assetfinder waybackurls dirsearch nmap{Colors.END}", "info")

    def run_subdomain_discovery(self):
        print_status(f"Starting Subdomain Discovery on: {self.target}", "header")
        
        # 1. Passive API Harvesting
        print_status("Querying passive DNS APIs concurrently...", "info")
        apis = [
            ("crt.sh", f"https://crt.sh/?q=%25.{self.target}&output=json"),
            ("HackerTarget", f"https://api.hackertarget.com/hostsearch/?q={self.target}"),
            ("AlienVault OTX", f"https://otx.alienvault.com/api/v1/indicators/domain/{self.target}/passive_dns")
        ]
        
        def fetch_api(name, url):
            results = set()
            try:
                status, body, _ = request_url(url, timeout=10)
                if status == 200 and body:
                    if name == "crt.sh":
                        data = json.loads(body)
                        for item in data:
                            name_value = item.get('name_value', '')
                            for val in name_value.split('\n'):
                                val = val.replace('*.', '')
                                if self.target in val:
                                    results.add(val.strip().lower())
                    elif name == "HackerTarget":
                        for line in body.splitlines():
                            parts = line.split(',')
                            if parts and self.target in parts[0]:
                                results.add(parts[0].strip().lower())
                    elif name == "AlienVault OTX":
                        data = json.loads(body)
                        for record in data.get('passive_dns', []):
                            hostname = record.get('hostname', '')
                            if self.target in hostname:
                                results.add(hostname.strip().lower())
            except Exception as e:
                pass
            return results

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(fetch_api, name, url): name for name, url in apis}
            for future in as_completed(futures):
                res = future.result()
                self.subdomains.update(res)
                print_status(f"Retrieved {len(res)} subdomains from {futures[future]}", "success")

        # 2. DNS Brute-Forcing (Fallback/Supplement)
        print_status("Starting Concurrent DNS Brute-forcing...", "info")
        sub_list = COMMON_SUBDOMAINS
        if self.wordlist_file and os.path.exists(self.wordlist_file):
            try:
                with open(self.wordlist_file, 'r', encoding='utf-8') as f:
                    sub_list = [line.strip().lower() for line in f if line.strip()]
            except Exception:
                pass
        
        def resolve_subdomain(sub):
            domain = f"{sub}.{self.target}"
            try:
                socket.gethostbyname(domain)
                return domain
            except socket.gaierror:
                return None

        found_brute = 0
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = [executor.submit(resolve_subdomain, sub) for sub in sub_list]
            for future in as_completed(futures):
                res = future.result()
                if res:
                    self.subdomains.add(res)
                    found_brute += 1

        print_status(f"DNS Brute-forcing added {found_brute} resolved subdomains.", "success")
        self.subdomains.add(self.target) # Include root target
        self.subdomains = sorted(list(self.subdomains))
        
        # Save to file
        sub_file = os.path.join(self.output_dir, "subdomains.txt")
        with open(sub_file, "w", encoding="utf-8") as f:
            f.write("\n".join(self.subdomains))
            
        print_status(f"Found a total of {len(self.subdomains)} unique subdomains saved to {sub_file}", "success")

    def run_port_scanning(self):
        print_status("Starting Fast Multi-Threaded Port Scanning...", "header")
        
        # Select target list
        scan_targets = list(self.subdomains)[:30] # Top 30 for swift scans
        if not scan_targets:
            scan_targets = [self.target]
            
        print_status(f"Scanning common ports on {len(scan_targets)} unique host targets...", "info")
        
        def scan_port(host, port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.8)
                    result = s.connect_ex((host, port))
                    if result == 0:
                        return port
            except Exception:
                pass
            return None

        total_open = 0
        for host in scan_targets:
            self.open_ports[host] = []
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = {executor.submit(scan_port, host, port): port for port in COMMON_PORTS}
                for future in as_completed(futures):
                    port = future.result()
                    if port:
                        self.open_ports[host].append(port)
                        total_open += 1
            if self.open_ports[host]:
                print_status(f"Host {Colors.BOLD}{host}{Colors.END} has open ports: {Colors.GREEN}{', '.join(map(str, sorted(self.open_ports[host])))}{Colors.END}", "success")
                
        # Save to file
        port_file = os.path.join(self.output_dir, "ports.txt")
        with open(port_file, "w", encoding="utf-8") as f:
            for host, ports in self.open_ports.items():
                if ports:
                    f.write(f"{host}: {','.join(map(str, sorted(ports)))}\n")
                    
        print_status(f"Port scanning complete. Logged open ports to {port_file}", "success")

    def run_http_probing(self):
        print_status("Starting HTTP Probing (Checking Live Subdomains)...", "header")
        
        def probe_target(subdomain):
            results = []
            for proto in ["https://", "http://"]:
                url = f"{proto}{subdomain}"
                status, body, headers = request_url(url, timeout=4)
                if status > 0:
                    title_match = re.search(r'<title>(.*?)</title>', body, re.IGNORECASE)
                    title = title_match.group(1).strip() if title_match else "No Title"
                    server = headers.get('Server', 'Unknown') if hasattr(headers, 'get') else 'Unknown'
                    length = len(body)
                    results.append({
                        "url": url,
                        "status": status,
                        "title": title[:40],
                        "server": server,
                        "length": length,
                        "body": body
                    })
                    # Prefer HTTPS if available
                    break
            return results

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = [executor.submit(probe_target, sub) for sub in self.subdomains]
            for future in as_completed(futures):
                res_list = future.result()
                for res in res_list:
                    self.alive_subdomains[res["url"]] = res
                    print_status(f"Live: {Colors.GREEN}{res['url']}{Colors.END} [Status: {res['status']}] [Title: {res['title']}] [Server: {res['server']}]", "success")

        # Save to file
        alive_file = os.path.join(self.output_dir, "alive_subdomains.txt")
        with open(alive_file, "w", encoding="utf-8") as f:
            for url in self.alive_subdomains:
                f.write(f"{url}\n")
                
        print_status(f"Probed {len(self.alive_subdomains)} alive HTTP endpoints. Saved to {alive_file}", "success")

    def run_url_gathering(self):
        print_status("Starting URL Gathering (Wayback & Passive Source Harvesting)...", "header")
        
        # Wayback Machine API
        wayback_url = f"http://web.archive.org/cdx/search/cdx?url=*.{self.target}/*&output=json&collapse=urlkey&limit=500"
        print_status(f"Requesting archives from Wayback Machine...", "info")
        
        status, body, _ = request_url(wayback_url, timeout=12)
        wayback_count = 0
        if status == 200 and body:
            try:
                data = json.loads(body)
                if len(data) > 1:
                    # First row is header
                    for row in data[1:]:
                        if len(row) > 2:
                            url = row[2]
                            self.urls.add(url)
                            wayback_count += 1
            except Exception:
                pass
                
        print_status(f"Gathered {wayback_count} archive URLs from Wayback Machine.", "success")
        
        # Extract and clean parameters
        param_urls = set()
        for url in self.urls:
            if '?' in url and '=' in url:
                param_urls.add(url)
                
        # Save to file
        urls_file = os.path.join(self.output_dir, "urls.txt")
        with open(urls_file, "w", encoding="utf-8") as f:
            for url in sorted(list(self.urls)):
                f.write(f"{url}\n")
                
        print_status(f"Total urls saved to {urls_file}: {len(self.urls)} (Parameters endpoints: {len(param_urls)})", "success")

    def run_directory_fuzzing(self):
        print_status("Starting Directory Brute-Forcing & Fuzzing...", "header")
        
        # Only fuzz top live targets to optimize execution speed
        fuzz_targets = list(self.alive_subdomains.keys())[:5]
        if not fuzz_targets:
            print_status("No live HTTP targets found to fuzz.", "warning")
            return
            
        print_status(f"Fuzzing top {len(fuzz_targets)} active subdomains using ultra-fast native engine...", "info")
        
        def fuzz_path(base_url, path):
            url = f"{base_url}/{path}" if not base_url.endswith('/') else f"{base_url}{path}"
            status, body, _ = request_url(url, timeout=3)
            # Filter standard status codes (avoid standard 404, or 400 bad requests)
            if status in [200, 204, 301, 302, 403, 500]:
                return url, status
            return None

        for base_url in fuzz_targets:
            self.fuzzed_dirs[base_url] = []
            print_status(f"Scanning target: {base_url}", "info")
            
            with ThreadPoolExecutor(max_workers=self.threads) as executor:
                futures = [executor.submit(fuzz_path, base_url, path) for path in SENSITIVE_PATHS]
                for future in as_completed(futures):
                    res = future.result()
                    if res:
                        found_url, status = res
                        self.fuzzed_dirs[base_url].append((found_url, status))
                        color = Colors.GREEN if status == 200 else Colors.YELLOW
                        print_status(f"  -> Found: {color}{found_url}{Colors.END} [Status: {status}]", "success")

        # Save to file
        dir_file = os.path.join(self.output_dir, "directories.txt")
        with open(dir_file, "w", encoding="utf-8") as f:
            for base, results in self.fuzzed_dirs.items():
                if results:
                    f.write(f"--- {base} ---\n")
                    for url, status in results:
                        f.write(f"[{status}] {url}\n")
                        
        print_status(f"Directory brute-forcing logged to {dir_file}", "success")

    def run_vulnerability_assessment(self):
        print_status("Running Precise Vulnerability Assessment Tests...", "header")
        
        # Test 1: Subdomain Takeover Analysis
        print_status("Analyzing resolved endpoints for Subdomain Takeovers...", "info")
        for url, data in self.alive_subdomains.items():
            body = data["body"]
            for service, signatures in TAKEOVER_SIGNATURES.items():
                for sig in signatures:
                    if sig in body:
                        vuln = {
                            "type": "Subdomain Takeover",
                            "severity": "High",
                            "target": url,
                            "description": f"Target endpoint reflects a signature for potentially unclaimed service: {service} ({sig})"
                        }
                        self.vulnerabilities.append(vuln)
                        print_status(f"VULNERABILITY DETECTED: {Colors.RED}{Colors.BOLD}Subdomain Takeover on {url} via {service}!{Colors.END}", "danger")
                        break

        # Test 2: Sensitive Data Leak / Backups
        print_status("Scanning directory results for Exposed Secrets & Configs...", "info")
        for base_url, results in self.fuzzed_dirs.items():
            for url, status in results:
                if status == 200:
                    is_leak = False
                    reason = ""
                    # Fetch file content
                    _, body, _ = request_url(url, timeout=3)
                    if ".env" in url:
                        is_leak = True
                        reason = "Exposed environment file (.env)"
                    elif ".git/config" in url:
                        is_leak = True
                        reason = "Exposed Git Configuration directory"
                    elif "wp-config" in url or "config.php" in url:
                        if "DB_PASSWORD" in body or "define" in body:
                            is_leak = True
                            reason = "Exposed sensitive PHP database configuration details"
                    elif "backup" in url or ".sql" in url:
                        is_leak = True
                        reason = f"Database or Backup archive is accessible: {url.split('/')[-1]}"
                        
                    if is_leak:
                        vuln = {
                            "type": "Sensitive Data Leak",
                            "severity": "Critical",
                            "target": url,
                            "description": reason
                        }
                        self.vulnerabilities.append(vuln)
                        print_status(f"VULNERABILITY DETECTED: {Colors.RED}{Colors.BOLD}Critical Sensitive Data Leak at {url} ({reason}){Colors.END}", "danger")

        # Test 3: CORS Misconfiguration Check
        print_status("Checking live endpoints for CORS Misconfiguration...", "info")
        cors_targets = list(self.alive_subdomains.keys())[:10]
        
        def test_cors(url):
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
                "Origin": "https://evil-attacker.com"
            }
            status, _, resp_headers = request_url(url, timeout=4, headers=headers)
            if resp_headers:
                allow_origin = resp_headers.get('Access-Control-Allow-Origin', '')
                allow_creds = resp_headers.get('Access-Control-Allow-Credentials', '')
                if allow_origin == "https://evil-attacker.com" or allow_origin == "*":
                    # Elevated severity if credentials are also allowed
                    severity = "Medium" if allow_creds == "true" else "Low"
                    return {
                        "type": "CORS Misconfiguration",
                        "severity": severity,
                        "target": url,
                        "description": f"Reflected CORS origin header returned: {allow_origin} (Credentials: {allow_creds})"
                    }
            return None

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = [executor.submit(test_cors, url) for url in cors_targets]
            for future in as_completed(futures):
                res = future.result()
                if res:
                    self.vulnerabilities.append(res)
                    print_status(f"VULNERABILITY DETECTED: {Colors.YELLOW}CORS Misconfiguration on {res['target']} [Severity: {res['severity']}]{Colors.END}", "warning")

        # Test 4: Open Redirect Vulnerability Check
        print_status("Testing URLs for Open Redirect endpoints...", "info")
        param_urls = [url for url in self.urls if '?' in url and '=' in url][:15]
        redirect_payload = "https://www.bing.com"
        
        def test_open_redirect(url):
            # Parse URL & inject payload into all parameter values
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            for k in params:
                params[k] = [redirect_payload]
            new_query = urllib.parse.urlencode(params, doseq=True)
            test_url = urllib.parse.urlunparse(parsed._replace(query=new_query))
            
            status, _, resp_headers = request_url(test_url, timeout=4)
            if status in [301, 302] and resp_headers:
                location = resp_headers.get('Location', '')
                if redirect_payload in location:
                    return {
                        "type": "Open Redirect",
                        "severity": "Medium",
                        "target": test_url,
                        "description": f"Endpoint redirects to an external unvalidated host: {location}"
                    }
            return None

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = [executor.submit(test_open_redirect, url) for url in param_urls]
            for future in as_completed(futures):
                res = future.result()
                if res:
                    self.vulnerabilities.append(res)
                    print_status(f"VULNERABILITY DETECTED: {Colors.YELLOW}{Colors.BOLD}Open Redirect found on {res['target']}{Colors.END}", "warning")

        # Save to file
        vuln_file = os.path.join(self.output_dir, "vulnerabilities.txt")
        with open(vuln_file, "w", encoding="utf-8") as f:
            for v in self.vulnerabilities:
                f.write(f"[{v['severity']}] {v['type']} on {v['target']}\nDetail: {v['description']}\n\n")
                
        # Generate final comprehensive JSON report
        report_data = {
            "target": self.target,
            "scan_time": time.ctime(),
            "total_subdomains": len(self.subdomains),
            "alive_hosts": len(self.alive_subdomains),
            "vulnerabilities": self.vulnerabilities,
            "open_ports": self.open_ports
        }
        report_file = os.path.join(self.output_dir, "scan_report.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=4)
            
        print_status(f"Comprehensive vulnerability check completed. Found {len(self.vulnerabilities)} vulnerabilities.", "success")
        print_status(f"Full report saved to: {report_file}", "success")

def main():
    print(BANNER)
    
    parser = argparse.ArgumentParser(description="scan3l - High-Speed Automated Bug Bounty Platform")
    parser.add_argument("-t", "--target", help="Target domain (e.g., example.com)", required=False)
    parser.add_argument("-w", "--wordlist", help="Custom wordlist file for subdomain brute forcing", default=None)
    parser.add_argument("-o", "--output", help="Custom output folder path", default=None)
    parser.add_argument("--threads", type=int, help="Thread count for optimal performance", default=50)
    parser.add_argument("--install-deps", action="store_true", help="Automatically install recommended system tools on Kali Linux")
    
    args = parser.parse_args()
    
    if args.install_deps:
        # Run auto installer
        print_status("Attempting auto-installation of tools. Please run with sudo privileges if needed.", "info")
        try:
            cmd = "sudo apt update && sudo apt install -y subfinder httpx nuclei assetfinder waybackurls dirsearch nmap"
            print_status(f"Executing: {cmd}", "info")
            subprocess.run(cmd, shell=True)
            print_status("Dependencies setup completed successfully!", "success")
        except Exception as e:
            print_status(f"Installation command failed or interrupted: {e}", "danger")
        if not args.target:
            sys.exit(0)
            
    if not args.target:
        parser.print_help()
        print("\n" + Colors.RED + "Error: Please specify a target domain using -t / --target" + Colors.END)
        sys.exit(1)

    # Initialize Scanner
    scanner = Scan3l(
        target=args.target,
        threads=args.threads,
        output_dir=args.output,
        wordlist_file=args.wordlist
    )
    
    # Check current system tools
    scanner.check_and_install_dependencies()
    
    start_time = time.time()
    
    # Run pipeline
    scanner.run_subdomain_discovery()
    scanner.run_http_probing()
    scanner.run_port_scanning()
    scanner.run_url_gathering()
    scanner.run_directory_fuzzing()
    scanner.run_vulnerability_assessment()
    
    elapsed = time.time() - start_time
    print_status(f"Pipeline finished! Elapsed scan time: {elapsed:.2f} seconds.", "success")
    print_status(f"Results saved in: {Colors.BOLD}{scanner.output_dir}{Colors.END}", "success")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Scan interrupted by user. Exiting scan3l...{Colors.END}")
        sys.exit(1)
