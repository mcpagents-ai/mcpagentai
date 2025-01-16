from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from mcpagentai.core.agent_base import MCPAgent
from mcpagentai.defs import StockTools, StockGetPrice, StockGetTickerByNameAgent, StockGetPriceHistory
from mcpagentai.defs import GoogleDriveTools, GoogleDriveGetFileContent, GoogleDriveGetFilenames

from typing import Sequence, Union

import requests

import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload

import io
import pickle
import os


class GoogleDriveAgent(MCPAgent):
    def __init__(self, pickle_file: str | None = None):
        super().__init__()
        self.pickle_file = pickle_file
        if self.pickle_file is None:
            self.pickle_file = os.getenv("GOOGLE_PICKLE_PATH")
            if self.pickle_file is None:
                raise ValueError(f"Path to Google pickle file not provided")
    def list_tools(self) -> list[Tool]:
        return [
            Tool(name=GoogleDriveTools.GET_ALL_FILENAMES.value,
                 description="Get all filenames and id",
                 inputSchema={"type": "object",
                              "properties": {
                                  "number": {
                                      "type": "string",
                                      "description": "Number of file to list"
                                  }
                              }
                              }
                 ),
            Tool(name=GoogleDriveTools.GET_FILE_CONTENT.value,
                 description="Get content of file",
                 inputSchema={
                     "type": "object",
                     "properties":
                         {
                             "file_id":
                                 {
                                     "type": "string",
                                     "description": "File id in google drive. Currently supported mimetypes are text/ and application/json"
                                 },
                             "required": ["file_id"]
                         }
                 })
        ]

    def call_tool(self,
                  name: str,
                  arguments: dict) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        if name == GoogleDriveTools.GET_ALL_FILENAMES.value:
            return self._handle_get_filenames(arguments)
        elif name == GoogleDriveTools.GET_FILE_CONTENT.value:
            return self._handle_get_file_content(arguments)
        else:
            raise ValueError(f"Unknown tool value: {name}")

    def _handle_get_filenames(self, arguments: dict) -> Sequence[TextContent]:
        number = arguments.get("number")
        if number is None:
            number = 10
        result = self._get_filenames(number)
        return [
            TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
        ]

    def _handle_get_file_content(self, arguments: dict) -> Sequence[TextContent]:
        file_id = arguments.get("file_id")
        if file_id is None:
            raise ValueError("File id to Google drive file not provided")
        result = self._get_file_content(file_id)
        return [
            TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
        ]

    def _get_filenames(self, number) -> GoogleDriveGetFilenames:
        creds = self.__authenticate_pickle()
        # Build the Drive API service
        service = build('drive', 'v3', credentials=creds)

        # List files in the user's Google Drive
        results = service.files().list(
            pageSize=number, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            return GoogleDriveGetFilenames(filenames=[{}])
        else:
            filenames = []
            for item in items:
                print(f"{item['name']} ({item['id']})")
                filenames.append({"name": item['name'], "id": item['id']})
            return GoogleDriveGetFilenames(filenames=filenames)
        
    def _get_file_content(self, file_id) -> GoogleDriveGetFileContent:
        creds = self.__authenticate_pickle()
        service = build('drive', 'v3', credentials=creds)

        # Get the file's metadata
        file_metadata = service.files().get(fileId=file_id).execute()
        mime_type = file_metadata.get('mimeType')

        # Download the file content
        request = service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        # Decode the content if it's text or application/json (add support to other types later)
        if mime_type.startswith('text/') or mime_type.startswith('application/json'):
            file_str =  file_buffer.getvalue().decode('utf-8')
            return GoogleDriveGetFileContent(file_content=str(file_str))
        else:
            raise ValueError(f"Unsupported MIME type: {mime_type}")
    def __authenticate_pickle(self):
        creds = None
        # Load credentials from the token file if it exists
        if os.path.exists(self.pickle_file):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # Authenticate if no valid credentials exist
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            # Save the credentials for future use
            with open(self.pickle_file, 'wb') as token:
                pickle.dump(creds, token)

        return creds