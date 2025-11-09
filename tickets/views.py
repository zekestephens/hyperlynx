import time

from django.contrib.auth import logout as django_logout
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import os
from dotenv import load_dotenv

load_dotenv()

# Create your views here.
def index(request):
    return render(request, "index.html")

@login_required
def test_page(request):
    return render(request, "index.html")

def all_tickets(request):
    return render(request, "all_tickets.html") #testing dashboard

# def dashboard(request):
#     return render(request, "dashboard.html") #testing dashboard


@login_required
def dashboard(request):
    # Example: determine role based on user (you can replace this with your own logic)
    user_role = "engineer"
    # if request.user.groups.filter(name="DataTechnician").exists():
    #     user_role = "data_technician"

    return render(request, "dashboard.html", {"user_role": user_role})



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

def generate():
    client = genai.Client(
        api_key=os.getenv('GEMINI_API_KEY'),
    )
    model = "gemini-2.5-pro"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""INSERT_INPUT_HERE"""),
            ],
        ),
    ]
    tools = [
        types.Tool(googleSearch=types.GoogleSearch(
        )),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=-1,
        ),
        image_config=types.ImageConfig(
            image_size="1K",
        ),
        tools=tools,
        system_instruction=[
            types.Part.from_text(text="""You are the ticket master. Engineers come to you to make tickets about failures happening within the datacenter. You are looking for the following fields:
location (floor, hall, pod, aisle, and rack)
type
status (unassigned, assigned, working on, closed)
summary (short issue)
description (long form of issue)
assigned (list of people assigned to)
priority (lowest, low, medium, high, highest)
due date
labels
attachment
linked to (blocks, is blocked by, clones, is cloned by, duplicates, is duplicated by, relates to)

some of these fields can be left blank but the location, type, summary, priority

keep on prompting user until all necessary fields are filled. Once filled, write all given information as a json and nothing more.
"""),
        ],
    )

    for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
    ):
        print(chunk.text, end="")

@dataclass
class ticket:
    labels: List[str]
    summary: str
    description: str
    priority: str

    project_key: str = "DCM"
    issue_type: str = "Task"

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
                    "name": self.priority
                },
                "issuetype": {
                    "name": self.issue_type
                }
            }
        }
def pass_new_ticket(
        summary: str,
        description: str,
        priority: str,
        labels: List[str]
) -> str:
    """ Tool that accepts parsed ticket data from the user's prompt,
        creates a structured JIRATicket object, and processes it.

        Args:
            summary: The concise title of the ticket.
            description: The detailed body of the ticket.
            priority: The urgency level (e.g., 'High', 'Medium').
            labels: A list of tags to categorize the ticket.

        Returns:
            A confirmation message after processing the ticket.
        """
    ticket_ = ticket(
        summary=summary,
        description=description,
        priority=priority,
        labels=labels
    )

    print(ticket_.self_to_JSON())

    return f"Ticket success."

client=genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
TICKET_MASTER_PROMPT = """
You are the ticket master. Engineers come to you to make tickets about failures happening within the datacenter. You are looking for the following fields:
LOCATION (Must give a: floor, hall, pod, aisle, and rack)
SUMMARY (short issue)
DESCRIPTION
PRIORITY (Must be one of these 5 values: Lowest, Low, Medium, High, Highest)
LABELS

some of these fields can be left blank but the location, summary, priority must be filled.

keep on prompting user until all necessary fields are filled. 
Once all necessary fields are filled, 
using LOCATION, SUMMARY, DESCRIPTION generate one or two worded descriptions of this task store it as a JSON list of strings under LABELS

Pass it into the tool given to you.
"""


@csrf_exempt
def chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            history = data.get('history', '')
            #
            # tools = types.Tool.from_callable(
            #     func=pass_new_ticket,
            #     description="Tool to pass out the final JSON value. Requires the complete JIRA-style JSON structure as its only argument."
            # )
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


            history.append({
                "role": "user",
                "parts": [{"text": user_message}]
            })
            history.append({
                "role": "user",
                "parts": [{"text": user_message}]
            })

            if(isJSON(response.text)):
                print(response.text)
                # validate, and send off to make ticket
                return response.text

            # 3. Return AI response
            return JsonResponse({'reply': response.text})

        except Exception as e:
            print(f"Gemini API Error: {e}")
            return JsonResponse({'error': 'An error occurred while contacting the AI.'}, status=500)

    return JsonResponse({'detail': 'Method not allowed'}, status=405)