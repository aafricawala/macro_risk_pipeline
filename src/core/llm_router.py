"""
Module Name: llm_router.py
Repo Path: src/core/llm_router.py

BCBS 239 Data Lineage & Compliance Standards:
- Role: Zero-Hardcoding Dynamic Model Discovery and LLM Inference Router.
- Transformation: Programmatically discovers active models from Google AI Studio,
  parses version hierarchies, and sorts from most recent to oldest.
"""

# Import regular expressions module to parse model version numbers dynamically
import re

# Import time module to handle transient backoff delays
import time

# Import json module for parsing structured response text
import json

# Import typing primitives for strict type enforcement
from typing import List, Dict, Any, Optional, Tuple

# Import logger from loguru for structured diagnostic logs
from loguru import logger


# Helper function to extract a comparable version tuple from a model name string
def parse_model_version_tuple(model_name: str) -> Tuple[int, int, int, int]:
    # Convert name to lowercase for case-insensitive parsing
    clean_name = model_name.lower()
    # Prioritize 'flash' models (weight=2) over 'pro' (weight=1) and others (weight=0)
    tier_weight = 2 if "flash" in clean_name else (1 if "pro" in clean_name else 0)
    # Search for version pattern like 'gemini-2.5', 'gemini-3.0', 'gemini-1.5'
    version_match = re.search(r"gemini-(\d+)(?:\.(\d+))?(?:\.(\d+))?", clean_name)
    # Check if a numerical version was matched in the model name
    if version_match:
        # Extract major version number (defaults to 0 if None)
        major = int(version_match.group(1)) if version_match.group(1) else 0
        # Extract minor version number (defaults to 0 if None)
        minor = int(version_match.group(2)) if version_match.group(2) else 0
        # Extract patch version number (defaults to 0 if None)
        patch = int(version_match.group(3)) if version_match.group(3) else 0
        # Return composite sort key tuple: (tier_weight, major, minor, patch)
        return (tier_weight, major, minor, patch)
    # Return zero tuple if no version pattern was found
    return (tier_weight, 0, 0, 0)


# Function to query Google AI Studio and dynamically sort available models from newest to oldest
def discover_and_sort_available_models(client) -> List[str]:
    # Initialize empty list to store valid generation models
    discovered_models: List[str] = []
    # Try querying the live API models catalog
    try:
        # Iterate over all models returned by the API client
        for model_obj in client.models.list():
            # Extract raw model identifier string
            raw_id = getattr(model_obj, "name", "")
            # Strip the 'models/' namespace prefix if present
            clean_id = raw_id.replace("models/", "").strip()
            # Filter: include only Gemini generation models (exclude embeddings, imagen, and audio)
            if "gemini" in clean_id.lower() and not any(
                bad_kw in clean_id.lower() for bad_kw in ["embedding", "imagen", "aqa", "tts", "whisper"]
            ):
                # Add candidate model to discovered list
                discovered_models.append(clean_id)
        # Sort discovered models from newest to oldest using version parsing key in reverse order
        sorted_models = sorted(discovered_models, key=parse_model_version_tuple, reverse=True)
        # Check if at least one model was found
        if sorted_models:
            # Log successful dynamic discovery
            logger.info(f"LLM Router: Dynamically discovered {len(sorted_models)} active models: {sorted_models}")
            # Return dynamically sorted model identifiers
            return sorted_models
    # Catch any error during dynamic model discovery (e.g. network failure or permissions)
    except Exception as discovery_error:
        # Log warning regarding discovery failure
        logger.warning(f"Dynamic model discovery failed: {discovery_error}. Falling back to default list.")
    # Return minimal fallback list if dynamic discovery encountered an error
    return ["gemini-2.5-flash", "gemini-1.5-flash"]


# Main dynamic execution function that automatically discovers and calls the newest available model
def execute_dynamic_json_query(
    prompt: str,
    api_key: str,
    candidate_models: Optional[List[str]] = None,
    response_schema: Optional[Any] = None,
    temperature: float = 0.0,
) -> Tuple[Dict[str, Any], str]:
    # Import Google GenAI library inside function for clean test isolation
    from google import genai
    from google.genai import types

    # Initialize Google GenAI client with provided API key
    client = genai.Client(api_key=api_key)
    # If candidate models were not supplied, dynamically discover them from the API
    models_to_try = candidate_models or discover_and_sort_available_models(client)
    # Print the discovered prioritized model order to the screen
    print(f"[LLM Router] Discovered {len(models_to_try)} available models in priority order:")
    # Print top candidate models
    for idx, m_name in enumerate(models_to_try[:4], 1):
        # Print numbered model name
        print(f"  {idx}. {m_name}")
    # Container to collect errors for diagnostic traceability
    errors_encountered: List[str] = []

    # Iterate through models from newest to oldest
    for model_name in models_to_try:
        # Attempt up to 2 times to handle transient 503 load spikes
        for attempt in range(2):
            # Encapsulate model query in try-except block
            try:
                # Announce model attempt
                print(f"[LLM Router] Trying model '{model_name}' (Attempt {attempt + 1})...")
                # Log model attempt
                logger.info(f"LLM Router: Attempting query with model: {model_name} (Attempt {attempt + 1})")

                # Configure generation options dictionary
                config_kwargs: Dict[str, Any] = {
                    "response_mime_type": "application/json",
                    "temperature": temperature,
                }
                # Attach response schema if provided for strict Pydantic enforcement
                if response_schema is not None:
                    # Assign schema to config dictionary
                    config_kwargs["response_schema"] = response_schema

                # Build GenerateContentConfig object
                config = types.GenerateContentConfig(**config_kwargs)
                # Send generation request to Gemini API
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )

                # Verify that response text was returned
                if not response.text:
                    # Raise error if response body is empty
                    raise ValueError(f"Empty response body received from {model_name}.")

                # Parse JSON text into dictionary
                parsed_dict = json.loads(response.text)
                # Print confirmation of successful model execution
                print(f"[LLM Router] SUCCESS: Selected and verified response from '{model_name}'")
                # Log success message
                logger.info(f"LLM Router: Successfully generated response using {model_name}")
                # Return parsed JSON dictionary and name of the model that succeeded
                return parsed_dict, model_name

            # Catch exceptions during model query
            except Exception as exc:
                # Convert exception to string
                err_str = str(exc)
                # If 503 temporary overload on first attempt, sleep 2 seconds and retry
                if "503" in err_str and attempt == 0:
                    # Print 503 warning
                    print(f"[LLM Router] 503 spike on '{model_name}'. Retrying in 2 seconds...")
                    # Sleep for 2 seconds
                    time.sleep(2)
                    # Continue to attempt 2
                    continue
                # Format failure message
                err_msg = f"Model '{model_name}' failed ({type(exc).__name__}: {err_str})"
                # Log warning
                logger.warning(f"LLM Router: {err_msg}. Cascading to next candidate...")
                # Print warning to screen
                print(f"[LLM Router] WARNING: {err_msg}. Falling back...")
                # Record error in trace history
                errors_encountered.append(err_msg)
                # Break attempt loop to move to the next model in the sorted list
                break

    # If all discovered models failed, raise consolidated runtime exception
    raise RuntimeError(f"All dynamically discovered models failed. Details: {' | '.join(errors_encountered)}")
