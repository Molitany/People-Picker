import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request
import service

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
app = Flask(__name__)

if (not os.path.exists("developers.json")):
    open('developers.json', 'x').close()
if (not os.path.exists("dev_stack.json")):
    open('dev_stack.json', 'x').close()

service.AuthorizeGithubInstallation()

@app.route('/github/events', methods=['POST'])
def GithubEvent():
    action = request.json.get('action')
    if (action == 'opened' or action == 'reopened'):
        pr = request.json.get('pull_request')
        if (not bool(pr.get('requested_reviewers')) and not bool(pr.get('assignees'))):
            service.AssignReviewers(request.json.get('pull_request'))
    return "return"

if __name__ == "__main__": 
    app.run(debug=True)