import os
import shutil
import deploy_config

def run(cmd):
    # https://stackoverflow.com/questions/26369829/subprocess-popen-handling-stdout-and-stderr-as-they-come
    import sys, subprocess
    p = subprocess.Popen(cmd,
                         stdout=sys.stdout,
                         stderr=sys.stderr)

    # https://stackoverflow.com/questions/33496416/kill-subprocess-call-after-keyboardinterrupt
    try:
        p.wait()
    except KeyboardInterrupt:
        try:
           #p.terminate()
            p.send_signal(signal.SIGINT)
        except OSError:
           pass
        p.wait()

os.chdir(os.path.dirname(deploy_config.modpackZipfileName))
try:
    # Try nodejs http-server, in case it happens to be installed ( https://www.npmjs.com/package/http-server )
    run([shutil.which('http-server')])
    #run([shutil.which('dir')])
except:
    # Fallback on built-in python http server
    from http.server import HTTPServer, SimpleHTTPRequestHandler

    httpd = HTTPServer(('', 8080), SimpleHTTPRequestHandler)
    httpd.serve_forever()
