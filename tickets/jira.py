import os
from typing import Optional, Dict, List, Any
import requests
from dotenv import load_dotenv

from tickets.tools import Priority


class JiraClient:
    """
    A client for interacting with the Jira REST API.

    Usage:
        client = JiraClient(
            base_url="https://jira.hyperlynx.us",
            token="your_token_here"
        )

        # Or load from environment
        client = JiraClient.from_env()
    """

    def __init__(self, base_url: str, token: str, username: Optional[str] = None):
        """
        Initialize the Jira client.

        Args:
            base_url: The base URL of your Jira instance (e.g., https://jira.hyperlynx.us)
            token: Personal Access Token or API token
            username: Optional username (only needed for Basic Auth with API tokens)
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.username = username

        # Set up authentication headers
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    @classmethod
    def from_env(cls, env_file: str = ".env") -> "JiraClient":
        """
        Create a JiraClient from environment variables.

        Expected environment variables:
            JIRA_URL: Base URL of Jira instance
            JIRA_TOKEN: Personal Access Token or API token
            JIRA_USERNAME: (Optional) Username for Basic Auth

        Args:
            env_file: Path to .env file

        Returns:
            JiraClient instance
        """
        load_dotenv(env_file)

        base_url = os.getenv("JIRA_URL", "https://jira.hyperlynx.us")
        token = os.getenv("JIRA_TOKEN")
        username = os.getenv("JIRA_USERNAME", "zeke")

        if not token:
            raise ValueError("JIRA_TOKEN environment variable is required")

        return cls(base_url=base_url, token=token, username=username)

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request to the Jira API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response

    def get_current_user(self) -> Dict[str, Any]:
        """
        Get information about the currently authenticated user.

        Returns:
            Dictionary containing user information

        Example:
            user = client.get_current_user()
            print(f"Logged in as: {user['displayName']}")
        """
        response = self._request("GET", "/rest/api/2/myself")
        return response.json()

    def get_user(self, username: str) -> Dict[str, Any]:
        """
        Get information about a specific user.

        Args:
            username: The username to look up

        Returns:
            Dictionary containing user information

        Example:
            user = client.get_user("zeke")
            print(f"Email: {user['emailAddress']}")
        """
        response = self._request(
            "GET",
            "/rest/api/2/user",
            params={"username": username}
        )
        return response.json()

    def create_issue(
            self,
            project_key: str,
            summary: str,
            issue_type: str = "Task",
            description: Optional[str] = None,
            priority: str = "Medium",
            assignee: Optional[str] = None,
            custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new issue in Jira.

        Args:
            project_key: Project key (e.g., "DCM")
            summary: Issue summary/title
            issue_type: Type of issue (e.g., "Task", "Bug", "Story")
            description: Optional issue description
            priority: Optional priority (e.g., "High", "Medium", "Low")
            assignee: Optional assignee username
            custom_fields: Optional dict of custom field IDs and values
                          e.g., {"customfield_10001": "Building A"}

        Returns:
            Dictionary containing the created issue information

        Example:
            issue = client.create_issue(
                project_key="DCM",
                summary="Fix the login bug",
                issue_type="Bug",
                priority="High",
                assignee="zeke",
                custom_fields={"customfield_10001": "New York Office"}
            )
            print(f"Created: {issue['key']}")
        """
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": "Task"}
        }

        if description:
            fields["description"] = description

        if priority:
            fields["priority"] = {"name": priority}

        if assignee:
            fields["assignee"] = {"name": assignee}

        # Add custom fields
        if custom_fields:
            fields.update(custom_fields)

        issue_data = {"fields": fields}

        try:
            response = self._request("POST", "/rest/api/2/issue", json=issue_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"Error: {e}")
            print(f"Response: {e.response.text}")  # This shows the actual error
            raise

    def get_user_issues(
            self,
            username: Optional[str] = None,
            max_results: int = 50,
            status: Optional[str] = None,
            project: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get issues assigned to a specific user.

        Args:
            username: Username to get issues for (None = current user)
            max_results: Maximum number of results to return
            status: Optional status filter (e.g., "In Progress", "Done")
            project: Optional project key filter (e.g., "DCM")

        Returns:
            List of issue dictionaries

        Example:
            # Get my open issues
            issues = client.get_user_issues(status="In Progress")
            for issue in issues:
                print(f"{issue['key']}: {issue['fields']['summary']}")
        """
        # Build JQL query
        if username is None:
            jql = "assignee = currentUser()"
        else:
            jql = f"assignee = {username}"

        if status:
            jql += f" AND status = '{status}'"

        if project:
            jql += f" AND project = {project}"

        jql += " ORDER BY created DESC"

        response = self._request(
            "GET",
            "/rest/api/2/search",
            params={
                "jql": jql,
                "maxResults": max_results
            }
        )

        results = response.json()
        return results.get('issues', [])

    def get_all_issues(
            self,
            project: Optional[str] = None,
            max_results: int = 100,
            order_by: str = "created",
            order_direction: str = "DESC"
    ) -> List[Dict[str, Any]]:
        """
        Get all issues, optionally filtered by project.

        Args:
            project: Optional project key to filter by (e.g., "DCM")
            max_results: Maximum number of results to return
            order_by: Field to sort by (e.g., "created", "updated", "priority")
            order_direction: Sort direction ("ASC" or "DESC")

        Returns:
            List of issue dictionaries sorted by the specified field

        Example:
            # Get all DCM issues sorted by creation date
            issues = client.get_all_issues(project="DCM", max_results=200)

            # Get all issues sorted by update date
            issues = client.get_all_issues(order_by="updated")
        """
        # Build JQL query
        if project:
            jql = f"project = {project}"
        else:
            jql = "project is not EMPTY"

        jql += f" ORDER BY {order_by} {order_direction}"

        response = self._request(
            "GET",
            "/rest/api/2/search",
            params={
                "jql": jql,
                "maxResults": max_results
            }
        )

        results = response.json()
        return results.get('issues', [])

    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Get a specific issue by its key.

        Args:
            issue_key: Issue key (e.g., "DCM-123")

        Returns:
            Dictionary containing issue information

        Example:
            issue = client.get_issue("DCM-123")
            print(f"Status: {issue['fields']['status']['name']}")
        """
        response = self._request("GET", f"/rest/api/2/issue/{issue_key}")
        return response.json()

    def update_issue(
            self,
            issue_key: str,
            fields: Dict[str, Any]
    ) -> None:
        """
        Update an existing issue.

        Args:
            issue_key: Issue key (e.g., "DCM-123")
            fields: Dictionary of fields to update

        Example:
            client.update_issue(
                "DCM-123",
                {
                    "summary": "Updated summary",
                    "priority": {"name": "High"},
                    "customfield_10001": "New Location"
                }
            )
        """
        self._request(
            "PUT",
            f"/rest/api/2/issue/{issue_key}",
            json={"fields": fields}
        )

    def is_issue_done(self, issue_key: str) -> bool:
        """
        Check if an issue is in a "Done" status.

        Args:
            issue_key: Issue key (e.g., "DCM-123")

        Returns:
            True if the issue is done, False otherwise

        Example:
            if client.is_issue_done("DCM-123"):
                print("Task completed!")
        """
        issue = self.get_issue(issue_key)
        status_category = issue['fields']['status']['statusCategory']['key']
        return status_category == 'done'

    def get_project(self, project_key: str) -> Dict[str, Any]:
        """
        Get information about a project.

        Args:
            project_key: Project key (e.g., "DCM")

        Returns:
            Dictionary containing project information
        """
        response = self._request("GET", f"/rest/api/2/project/{project_key}")
        return response.json()

    def search_issues(
            self,
            jql: str,
            max_results: int = 50,
            fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for issues using JQL (Jira Query Language).

        Args:
            jql: JQL query string
            max_results: Maximum number of results
            fields: Optional list of fields to return

        Returns:
            List of matching issues

        Example:
            # Find high priority bugs
            issues = client.search_issues(
                'project = DCM AND issuetype = Bug AND priority = High'
            )

            # Find issues updated in the last week
            issues = client.search_issues(
                'updated >= -1w ORDER BY updated DESC'
            )
        """
        params = {
            "jql": jql,
            "maxResults": max_results
        }

        if fields:
            params["fields"] = ",".join(fields)

        response = self._request("GET", "/rest/api/2/search", params=params)
        results = response.json()
        return results.get('issues', [])
