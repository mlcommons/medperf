#!/usr/bin/env bash
echo "Preparing local medperf server..."
# we are located at /workspaces/medperf/ where repo is cloned to
pip install -e ./cli
pip install -r server/requirements.txt
pip install -r server/test-requirements.txt
medperf profile activate local

bash tutorials_scripts/setup_webui_tutorial.sh
cd server
cp .env.local.local-auth.sqlite .env

# patch to deal with how codespaces handle port forwarding
sed -i "1i import os" /workspaces/medperf/cli/medperf/web_ui/common.py
sed -i "1i import jinja2" /workspaces/medperf/cli/medperf/web_ui/common.py
sed -i "s|http://{host}:{port}/security_check?|http://\{os.environ.get('CODESPACE_NAME', 'localhost')\}-\{port\}.app.github.dev/security_check?|g" /workspaces/medperf/cli/medperf/web_ui/common.py
cat << 'EOF' >> /workspaces/medperf/cli/medperf/web_ui/common.py

@jinja2.pass_context
def relative_url_for(context, name, **path_params) -> str:
    return context["request"].url_for(name, **path_params).path


templates.env.globals["url_for"] = relative_url_for
EOF

sed -i 's#str(Path.home())#"/workspaces/medperf/medperf_tutorial"#g' /workspaces/medperf/cli/medperf/web_ui/api/routes.py

cd ..
