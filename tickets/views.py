import time

from django.contrib.auth import logout as django_logout
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import os
from json import dumps as json_dump

from django.utils.safestring import mark_safe
from dotenv import load_dotenv

from tickets.jira import JiraClient

load_dotenv()

# Create your views here.
def index(request):
    return render(request, "index.html")

def all_tickets(request):


    j = JiraClient(base_url=os.getenv("JIRA_URL"), token=os.getenv("JIRA_TOKEN"))

    issues =  [
        {
            'id': issue['id'],
            'title': issue['fields']['summary'],
            'date': issue['fields']['created'],
            'priority': issue['fields']['priority']['name']
        } for issue in j.get_all_issues()
    ]

    return render(request, "all_tickets.html", context=dict(issues=mark_safe(issues))) #testing dashboard

# def dashboard(request):
#     return render(request, "dashboard.html") #testing dashboard

@login_required
def dashboard(request):
    # Example: determine role based on user (you can replace this with your own logic)
    user_role = "engineer"
    # if request.user.groups.filter(name="DataTechnician").exists():
    #     user_role = "data_technician"

    j = JiraClient(base_url=os.getenv("JIRA_URL"), token=os.getenv("JIRA_TOKEN"))

    issues =  [
        {
            'id': issue['id'],
            'title': issue['fields']['description'],
            'date': issue['fields']['created'],
            'priority': issue['fields']['priority']['name']
        } for issue in j.get_all_issues()
    ]

    return render(request, "dashboard.html", {"user_role": user_role, "issues": mark_safe(json_dump(issues))})
#* Jira Get
def getUserTickets(request, username: str):
    j = JiraClient(base_url=os.getenv("JIRA_URL"), token=os.getenv("JIRA_TOKEN"))
    issues =  [
        {
            'id': issue['id'],
            'title': issue['fields']['summary'],
            'date': issue['fields']['created'],
            'priority': issue['fields']['priority']['name']
        } for issue in j.get_user_issues(username=request.user.jira_username)
    ]

    return render(request, "all_tickets.html", context=dict(issues=mark_safe(issues))) #testing dashboard



#* GEMINI!!!!!!!=====================================================================
# Imports*****
import base64

from google import genai
from google.genai import types
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from dataclasses import dataclass
from typing import List
from typing import Dict, Any
import json
#* Checks to see if string returned is JSON.
#  IF IS JSON:          return true
#                       return false
def isJSON(string_to_validate):
    try:
        json.loads(string_to_validate)
        return True
    except json.JSONDecodeError:
        return False
    except TypeError:
        return False

    # We can add a property to make it easy to get the string name
    @property
    def name_string(self):
        return self.value

    def self_to_JSON(self)-> Dict[str, Any]:
        return {
            "fields": {
                "project": {
                    "key": self.project_key
                },
                "labels": self.labels,
                "summary": self.summary,
                "description": self.description,
                "priority": {
                    "name": self.priority.value
                },
                "customfield_10200": self.location,
                "issuetype": {
                    "name": self.issue_type
                }
            }
        }
def pass_new_ticket(
        summary: str,
        description: str,
        priority: str,
        labels: List[str],
        location: str
) -> dict[str, Any]:
    """ Tool that accepts parsed ticket data from the user's prompt,
        creates a structured JIRATicket object, and processes it.

        Args:
            summary: The concise title of the ticket.
            description: The detailed body of the ticket.
            priority: The urgency level (e.g., 'High', 'Medium').
            labels: A list of tags to categorize the ticket.
            location: A string formatted FLOOR:HALL:POD:AISLE:RACK

        Returns:
            The result of creating a new ticket
        """
    api_client = JiraClient(base_url=os.getenv("JIRA_URL"), token=os.getenv("JIRA_TOKEN"))

    response = api_client.create_issue("DCM", summary, description=description, priority=priority, custom_fields={
        "customfield_10200": location,
    })

    return response

client=genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
TICKET_MASTER_PROMPT = """
You are the ticket master. Engineers come to you to make tickets about failures happening within the datacenter. You are looking for the following fields:
LOCATION (Must give a: floor, hall, pod, aisle, and rack, must have all 5 with no other locations)
SUMMARY (short issue)
DESCRIPTION
PRIORITY (Must be one of these 5 values: Lowest, Low, Medium, High, Highest)
LABELS

some of these fields can be left blank but the location, summary, priority must be filled.

keep on prompting user until all necessary fields are filled. 
Once all necessary fields are filled, 
using LOCATION, SUMMARY, DESCRIPTION generate one or two worded descriptions of this task store it as a JSON list of strings under LABELS
reformat LOCATION to match the "FLOOR:HALL:POD:AISLE:RACK" format

Pass it into the tool given to you.
Thank the user, do not prompt the user for any more things.
"""


@csrf_exempt
def chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            history = data.get('history', '')
            chat = client.chats.create(model="gemini-2.5-flash",
                                       history= history,
                                       config=types.GenerateContentConfig(
                                           system_instruction=TICKET_MASTER_PROMPT,
                                           tools=[pass_new_ticket]
                                       )
                                       )


            if not user_message:
                return JsonResponse({'error': 'Message cannot be empty'}, status=400)

            response = chat.send_message(user_message)
            if response.function_calls:
                print("It beckons")
                return JsonResponse({'done':True,'reply': response.text})


            history.append({
                "role": "user",
                "parts": [{"text": user_message}]
            })
            history.append({
                "role": "user",
                "parts": [{"text": user_message}]
            })


            # 3. Return AI response
            return JsonResponse({'done':True, 'reply': response.text})

        except Exception as e:
            print(f"Gemini API Error: {e}")
            return JsonResponse({'error': 'An error occurred while contacting the AI.'}, status=500)

    return JsonResponse({'detail': 'Method not allowed'}, status=405)