import logging
import re
import openai
from openai import OpenAI
import os
from typing import List
from fastapi import FastAPI
from pathlib import Path
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

app = FastAPI()

