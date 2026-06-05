import base64
import os

with open('client_secrets.json', 'rb') as f:
    client_b64 = base64.b64encode(f.read()).decode('utf-8')

with open('token_channel1.pickle', 'rb') as f:
    token_b64 = base64.b64encode(f.read()).decode('utf-8')

with open('secrets_for_github.md', 'w') as f:
    f.write("# GitHub Secrets\n\n")
    f.write("Copy the following text exactly as shown and paste it into GitHub.\n\n")
    f.write("## Secret Name: `CLIENT_SECRETS_B64`\n")
    f.write("```\n")
    f.write(client_b64)
    f.write("\n```\n\n")
    f.write("## Secret Name: `TOKEN_PICKLE_B64`\n")
    f.write("```\n")
    f.write(token_b64)
    f.write("\n```\n")
