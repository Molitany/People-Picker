import random
from sys import getdefaultencoding
from jwt import (
    JWT,
    jwk_from_pem
)
from jwt.utils import get_int_from_datetime
from datetime import datetime, timedelta, timezone
import os
import requests
import json
import shutil


def SaveUsersToFile(userList):
    members = getTeamMembers()

    with open('developers.json', 'r+') as file:
        fileText = file.read()
        file.seek(0)

        if (fileText == ''):
            devDict = {}
        else:
            devDict = json.loads(fileText)

        devDict.update(members)

        file.write(json.dumps(devDict))
        file.close()

    shutil.copy('developers.json', 'dev_stack.json')
    userList = json.loads(open('dev_stack.json', 'r').read())
    return userList


def getTeamMembers():
    developers = {}
    AuthorizeGithubInstallation()
    org = os.environ.get('ORG')
    token = os.environ.get('INSTALL_TOKEN')
    teams = requests.get(f"https://api.github.com/orgs/{org}/teams", headers={
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    }).json()
    for team in teams:
        slug = team.get('slug')
        _team = requests.get(f"https://api.github.com/orgs/{org}/teams/{slug}", headers={
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json'
        }).json()

        if (_team.get('parent') != None and _team.get('parent').get('name') == '2021E'):
            members = requests.get(f"https://api.github.com/orgs/{org}/teams/{slug}/members", headers={
                'Authorization': f'Bearer {token}',
                'Accept': 'application/vnd.github.v3+json'
            }).json()

            for member in members:
                if (member.get('login') != 'AAUGiraf'):
                    developers[member.get('login')] = slug

    return developers


def PRAssignedToUsers(userList, PROwnerName):
    if(len(userList) > 1):
        user0 = GetDeveloper(userList, PROwnerName)
        user1 = GetDeveloper(userList, PROwnerName)
    elif(len(userList) == 1):
        if (list(userList.values())[0] == PROwnerName):
            userList = SaveUsersToFile(userList)
            user0 = GetDeveloper(userList, PROwnerName)
            user1 = GetDeveloper(userList, PROwnerName)
        else:
            user0, user0ID = GetDeveloper(userList, PROwnerName)
            userList = SaveUsersToFile(userList)
            userList.pop(user0ID)
            user1 = GetDeveloper(userList, PROwnerName)
    else:
        userList = SaveUsersToFile(userList)
        user0 = GetDeveloper(userList, PROwnerName)
        user1 = GetDeveloper(userList, PROwnerName)

    with open('dev_stack.json', 'w') as file:
        file.write(json.dumps(userList))

    return [user0, user1]


def GetUsersFromFile(userList):
    with open('dev_stack.json', 'r') as outfile:
        text = outfile.read()
        if (text == ''):
            outfile.close()
            return SaveUsersToFile(userList)
        else:
            return json.loads(text)


def GetGithubInstallations():
    with open('Github_private_key.pem', 'rb') as pem:
        privateKey = jwk_from_pem(pem.read())

    ghToken = JWT().encode({
        'iat': get_int_from_datetime(datetime.now(timezone.utc)),
        'exp': get_int_from_datetime(datetime.now(timezone.utc) + timedelta(minutes=5)),
        'iss': os.environ.get('GIT_APP_ID')
    }, privateKey, alg='RS256')
    os.environ['JWT'] = ghToken

    response = requests.get("https://api.github.com/app/installations", headers={
        'Authorization': f'Bearer {ghToken}',
        'Accept': 'application/vnd.github.v3+json'
    }).json()

    return response


def AuthorizeGithubInstallation():
    installations = GetGithubInstallations()
    JWT = os.environ.get('JWT')
    response = requests.post(installations[0].get('access_tokens_url'), headers={
        'Authorization': f'Bearer {JWT}',
        'Accept': 'application/vnd.github.v3+json'
    }).json()
    if (response.get('token') is not None):
        os.environ['INSTALL_TOKEN'] = response.get('token')


def AssignReviewers(pullRequest, userList):
    PRUrl = pullRequest.get('url')
    assignees = PRAssignedToUsers(
        userList, pullRequest.get('user').get('login'))
    AuthorizeGithubInstallation()
    PostReviewers(PRUrl, assignees)


def PostReviewers(PRUrl, assignees):
    INSTALL_TOKEN = os.environ.get('INSTALL_TOKEN')
    json = {
        'reviewers': assignees
    }
    requests.post(f'{PRUrl}/requested_reviewers', headers={
        'Authorization': f'Bearer {INSTALL_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }, json=json)


def GetDeveloper(userList, name):
    DevName, DevTeam = random.choice(list(userList.items()))
    if (DevName == name or DevTeam == userList.get(name)):
        return GetDeveloper(userList, DevName)
    else:
        userList.pop(DevName)
        return DevName
