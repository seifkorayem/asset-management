import os
import json
import re
from fastapi import HTTPException
from pydantic import ValidationError

from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel
import time

from app.schemas import AssetFilter, AssetSummaryResponse
from app.logger import logger

MODEL = "gemini-2.5-flash"

AI_CACHE = {}
CACHE_TTL = 300  # 5 minutes

def get_cached(key: str):
    item = AI_CACHE.get(key)

    if item is None:
        return None

    if time.time() > item["expires"]:
        del AI_CACHE[key]
        return None

    return item["data"]


def set_cached(key: str, value):
    AI_CACHE[key] = {
        "data": value,
        "expires": time.time() + CACHE_TTL
    }


class RiskSummaryResponse(BaseModel):
    severity: str
    summary: str
    impact: str
    recommendation: str


class AssetCategoryResponse(BaseModel):
    environment: str
    criticality: str

class ReportResponse(BaseModel):
    recommendations: str

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

SYSTEM_PROMPT = """
You are an Asset Management assistant.

Convert the user's request into JSON.

Allowed fields:

{
    "type": "domain | subdomain | ip_address | service | certificate | technology",
    "status": "active | stale | archived",
    "search": "text to search in asset value",
    "source": "asset source",
    "tag": "asset tag"
}

Examples:

User: show assets from security_scan
{
    "source":"security_scan"
}

User: find google
{
    "search":"google"
}

User: show production assets
{
    "tag":"production"
}

Return ONLY JSON.
"""


def parse_query(query: str):

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{SYSTEM_PROMPT}\n\nUser: {query}"
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    return json.loads(text)

def extract_json(text: str):
    # remove markdown fences
    text = re.sub(r"```json|```", "", text).strip()

    # extract first JSON block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in response: {text}")

    return json.loads(match.group())

def summarize_risk(asset_id, risk_data):

    cache_key = f"risk:{asset_id}"

    cached = get_cached(cache_key)

    if cached:
        return cached
    
    prompt = f"""
You are a Senior Cybersecurity Analyst specializing in Attack Surface Management (ASM).

Asset Risk Information:

Risk Score:
{risk_data["risk_score"]} / 100

Detected Findings:
{"\n".join(f"- {reason}" for reason in risk_data["reasons"])}

Return ONLY JSON:
{{
    "severity": "",
    "summary": "",
    "impact": "",
    "recommendation": ""
}}
"""

    print("Calling Gemini...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )

    try:
        result = RiskSummaryResponse.model_validate_json(response.text)

        set_cached(cache_key, result)

        return result

    except (ValidationError, json.JSONDecodeError):
        raise HTTPException(
            status_code=500,
            detail="Invalid AI response."
        )

def categorize_asset(asset):
    cache_key = f"category:{asset.id}"

    cached = get_cached(cache_key)

    if cached:
        return cached
    
    prompt = f"""
You are a Senior Cybersecurity Analyst specializing in Attack Surface Management (ASM).

Your task is to classify a single digital asset based ONLY on the information provided.

========================
Asset Information
========================

Domain:
{getattr(asset, "domain", "Unknown")}

Asset Type:
{getattr(asset, "type", "Unknown")}

Additional Information:
- IP Address: {getattr(asset, "ip_address", "Unknown")}
- Open Ports: {getattr(asset, "open_ports", "Unknown")}
- SSL Enabled: {getattr(asset, "ssl_enabled", "Unknown")}
- Technologies: {getattr(asset, "technologies", "Unknown")}

========================
Classification Rules
========================

Environment:
- "prod" = Live production system serving business operations or customers.
- "staging" = Pre-production, testing, QA, or user acceptance environment.
- "dev" = Development, internal testing, laboratory, or sandbox environment.

Criticality:
- "low" = Minimal business impact if compromised.
- "medium" = Moderate operational impact.
- "high" = Significant business impact or supports important services.
- "critical" = Core infrastructure, highly sensitive systems, or compromise would cause severe business disruption.

If there is insufficient information, make the most reasonable classification based only on the supplied asset information.

========================
Instructions
========================

DO:
- Use ONLY the supplied asset information.
- Infer the most likely environment.
- Infer the most appropriate criticality.
- Return exactly one environment value.
- Return exactly one criticality value.
- Use lowercase values only.
- Return valid JSON only.

DO NOT:
- Do not invent asset information.
- Do not mention vulnerabilities that were not provided.
- Do not explain your reasoning.
- Do not include confidence scores.
- Do not include notes or comments.
- Do not add extra fields.
- Do not wrap the response in Markdown.
- Do not use code fences.
- Do not include any text before or after the JSON.

========================
Allowed Values
========================

Environment:
- prod
- staging
- dev

Criticality:
- low
- medium
- high
- critical

========================
Output Format
========================

Return ONLY the following JSON structure:

{{
    "environment": "prod",
    "criticality": "high"
}}
"""
    print("🤖 Calling Gemini...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "environment": {
                        "type": "STRING",
                        "enum": ["prod", "staging", "dev"]
                    },
                    "criticality": {
                        "type": "STRING",
                        "enum": ["low", "medium", "high", "critical"]
                    }
                },
                "required": ["environment", "criticality"]
            }
        )
    )
    try:
        result = AssetCategoryResponse.model_validate_json(response.text)

        set_cached(cache_key, result)

        return result

    except (ValidationError, json.JSONDecodeError, ValueError):
        raise HTTPException(
            status_code=500,
            detail="Invalid AI categorization response."
        )
    
def generate_report(
    total_assets: int,
    expired_certificates: int,
    high_risk_assets: int
):
    prompt = f"""
You are a Senior Cybersecurity Analyst.

Generate a concise executive recommendation based ONLY on the supplied ASM statistics.

ASM Statistics

Total Assets:
{total_assets}

Expired Certificates:
{expired_certificates}

High Risk Assets:
{high_risk_assets}

Instructions

DO:
- Use ONLY the supplied statistics.
- Provide 2-4 sentences.
- Explain the overall security posture.
- Prioritize the most important remediation actions.

DO NOT:
- Invent vulnerabilities.
- Mention CVEs.
- Mention OWASP.
- Mention MITRE ATT&CK.
- Mention compliance.
- Mention information not provided.
- Use Markdown.

Output

Return ONLY valid JSON.

Return ONLY valid JSON.

{{
    "recommendations": "..."
}}
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    print(response.text)

    result = ReportResponse.model_validate_json(
        response.text
    )

    try:
        result = ReportResponse.model_validate_json(response.text)
        return result

    except ValidationError:
        print(response.text)
        raise HTTPException(
            status_code=500,
            detail="Invalid AI report response."
        )

def generate_filters(query: str):

    prompt = f"""
You are an Asset Search Assistant.

Convert the user's request into database filters.

Allowed fields:

- type
- status
- tag

Rules:

DO:
- Use only these fields.
- Return null if unknown.
- Return valid JSON.

DO NOT:
- Invent fields.
- Generate SQL.
- Explain anything.
- Use Markdown.

Example:

{{
    "type":"domain",
    "status":"active",
    "tag":"production"
}}

User Query:

{query}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return AssetFilter.model_validate_json(response.text)

def summarize_assets(assets):

    asset_list = []

    for asset in assets:

        asset_list.append({
            "type": asset.type,
            "value": asset.value,
            "status": asset.status,
            "tags": asset.tags
        })

    prompt = f"""
You are a Senior Cybersecurity Analyst.

Summarize ONLY the supplied assets.

Assets:

{json.dumps(asset_list, indent=2)}

Instructions

DO:
- Use ONLY these assets.
- Mention how many assets were found.
- Summarize patterns.
- If empty, say no matching assets were found.

DO NOT:
- Invent assets.
- Mention assets not listed.
- Guess information.
- Use Markdown.

Return ONLY JSON.

{{
    "summary":"..."
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return AssetSummaryResponse.model_validate_json(response.text)
def get_cached(key: str):

    item = AI_CACHE.get(key)

    if not item:
        return None

    if item["expires"] < time.time():
        del AI_CACHE[key]
        return None

    return item["data"]


def set_cached(key: str, value):

    AI_CACHE[key] = {
        "data": value,
        "expires": time.time() + CACHE_TTL,
    }


def clear_asset_cache(asset_id: str):

    AI_CACHE.pop(f"risk:{asset_id}", None)
    AI_CACHE.pop(f"category:{asset_id}", None)

class RiskSummaryResponse(BaseModel):
    severity: str
    summary: str
    impact: str
    recommendation: str


class AssetCategoryResponse(BaseModel):
    environment: str
    criticality: str


class ReportResponse(BaseModel):
    recommendations: str

def parse_json_response(text: str):

    text = re.sub(
        r"```json|```",
        "",
        text
    ).strip()

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if not match:
        raise HTTPException(
            status_code=500,
            detail="AI returned invalid JSON."
        )

    return match.group()


def call_gemini(
    prompt: str,
    response_model=None,
    config=None,
):

    try:

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=config
        )

        text = parse_json_response(
            response.text
        )

        if response_model:
            return response_model.model_validate_json(
                text
            )

        return json.loads(text)

    except ValidationError:

        raise HTTPException(
            status_code=500,
            detail="AI returned invalid JSON."
        )

    except Exception as e:

        logger.exception(e)

        raise HTTPException(
            status_code=500,
            detail="Gemini request failed."
        )
SEARCH_FILTER_PROMPT = """
You are an Asset Search Assistant.

Convert the user's request into database filters.

Allowed fields:

- type
- status
- tag

Return ONLY JSON.
"""

def generate_graph_relationships(assets: list[str]):
    cache_key = f"graph:{','.join(sorted(assets))}"

    cached = get_cached(cache_key)
    if cached:
        return cached

    prompt = f"""
You are generating a knowledge graph.

Assets:
{assets}

Return ONLY valid JSON:

{{
  "nodes": [
    {{"id": "A"}},
    {{"id": "B"}}
  ],
  "edges": [
    {{"from": "A", "to": "B", "label": "related"}}
  ]
}}

Rules:
- Only use given assets
- No extra explanation
- Keep it minimal
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    try:
        result = json.loads(response.text)

        set_cached(cache_key, result)

        return result

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Invalid AI graph response"
        )