"""
BHU-NETRA Git Repository Initialization & GitHub Push Helper Script
Initializes local git repository, creates commits, and configures remote.
"""

import subprocess
import os
import sys

def run_cmd(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def init_git():
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Initializing Git Repository in: {repo_dir}")
    
    code, out, err = run_cmd("git init", cwd=repo_dir)
    print(f"git init: {out}")
    
    code, out, err = run_cmd("git config user.name \"BHU-NETRA Enterprise Architect\"", cwd=repo_dir)
    code, out, err = run_cmd("git config user.email \"architect@bhu-netra.gov.in\"", cwd=repo_dir)
    
    code, out, err = run_cmd("git add .", cwd=repo_dir)
    print("Staged all BHU-NETRA files.")
    
    code, out, err = run_cmd("git commit -m \"Initial Commit: BHU-NETRA Satellite Ground Segment Enterprise Architecture & Microservices Suite\"", cwd=repo_dir)
    print(f"git commit output: {out}")

def push_to_github(repo_url=None, token=None):
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not repo_url:
        print("\n[NOTE] No GitHub repository URL provided. To push to GitHub, run:")
        print("   python scripts/init_git_repo.py <GITHUB_REPO_URL> [GITHUB_TOKEN]")
        print("   Example: python scripts/init_git_repo.py https://github.com/username/BHU-NETRA.git")
        return

    print(f"\nConfiguring remote origin: {repo_url}")
    run_cmd("git remote remove origin", cwd=repo_dir)
    
    if token and "github.com" in repo_url:
        # Embed token into URL if provided
        authenticated_url = repo_url.replace("https://", f"https://{token}@")
        run_cmd(f"git remote add origin {authenticated_url}", cwd=repo_dir)
    else:
        run_cmd(f"git remote add origin {repo_url}", cwd=repo_dir)
        
    code, out, err = run_cmd("git branch -M main", cwd=repo_dir)
    code, out, err = run_cmd("git push -u origin main", cwd=repo_dir)
    if code == 0:
        print("Successfully pushed BHU-NETRA codebase to GitHub!")
    else:
        print(f"Push failed (or authentication required): {err}")

if __name__ == '__main__':
    init_git()
    if len(sys.argv) > 1:
        repo_url_arg = sys.argv[1]
        token_arg = sys.argv[2] if len(sys.argv) > 2 else None
        push_to_github(repo_url_arg, token_arg)
    else:
        push_to_github()
