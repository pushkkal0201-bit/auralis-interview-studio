"""Optional local REA wrapper. Does not install tools or execute the target app."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description='Analyze your own supported JavaScript/Electron app with an installed REA CLI.')
    parser.add_argument('target',type=Path)
    parser.add_argument('--output',type=Path,default=Path('rea-analysis.json'))
    args=parser.parse_args()
    if not args.target.exists():parser.error('Target does not exist.')
    executable=shutil.which('rea')
    if not executable:parser.error('REA is not installed. Follow https://github.com/morluto/rea . Main RoleReady app does not need REA or Node.js.')
    try:
        result=subprocess.run([executable,'analyze-javascript-application',str(args.target.resolve()),'--json'],capture_output=True,text=True,encoding='utf-8',timeout=180,check=True)
        obj=json.loads(result.stdout)
    except subprocess.TimeoutExpired:parser.error('Analysis timed out after 180 seconds.')
    except subprocess.CalledProcessError:parser.error('REA analysis failed. Run the CLI directly to inspect its diagnostics.')
    except ValueError:parser.error('REA output was not JSON. Check your installed CLI version.')
    args.output.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'Wrote {args.output}. Review it for private data before importing. If larger than 12,000 characters, select a smaller JSON excerpt.')

if __name__=='__main__':main()
