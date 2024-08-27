import requests
import json
import traceback
from config import API_BASE_URL, HEADERS
from utils.logger import info, error, debug
from constants import DEFAULT_IMAGE_PARAMS
import copy
from queue_manager import queue_manager

async def generate_image_queued(prompt, custom_params=None):
    async def generate_wrapper():
        return generate_image(prompt, custom_params)
    return await queue_manager.run_coroutine(generate_wrapper())

async def check_image_status_queued(job_id):
    async def check_wrapper():
        return check_image_status(job_id)
    return await queue_manager.run_coroutine(check_wrapper())

async def retrieve_generated_image_queued(job_id):
    async def retrieve_wrapper():
        return retrieve_generated_image(job_id)
    return await queue_manager.run_coroutine(retrieve_wrapper())

def generate_image(prompt, custom_params=None):
    endpoint = f"{API_BASE_URL}/api/v2/generate/async"
    params = copy.deepcopy(DEFAULT_IMAGE_PARAMS)
    
    if custom_params:
        params.update(custom_params)
    
    params['prompt'] = prompt
    
    debug(f"Image generation parameters: {json.dumps(params, indent=2)}")
    info(f"Attempting to access endpoint: {endpoint}")
    debug(f"Headers: {json.dumps(HEADERS, indent=2)}")

    try:
        response = requests.post(endpoint, headers=HEADERS, json=params)
        debug(f"Response status code: {response.status_code}")
        debug(f"Response content: {response.text}")
        response.raise_for_status()
        data = response.json()

        debug(f"API response: {json.dumps(data, indent=2)}")

        if 'id' in data:
            info(f"Image generation initiated successfully. Job ID: {data['id']}")
            return {
                "success": True,
                "id": data['id'],
                "kudos": data.get('kudos')
            }
        else:
            error(f"Failed to initiate image generation. API response: {json.dumps(data, indent=2)}")
            return {
                "success": False,
                "statusCode": response.status_code,
                "errors": data.get('errors', []),
                "message": data.get('message', 'Unknown error')
            }

    except requests.exceptions.RequestException as e:
        error(f"Error: Unable to send generate image request. Details:\n{traceback.format_exc()}")
        return {
            "success": False,
            "statusCode": getattr(e.response, 'status_code', 0),
            "errors": [{"error": str(e)}],
            "message": f"Request failed: {str(e)}"
        }
    except Exception as e:
        error(f"Unexpected error in generate_image: {str(e)}\nTraceback:\n{traceback.format_exc()}")
        return {
            "success": False,
            "statusCode": 500,
            "errors": [{"error": "unexpected error"}],
            "message": f"An unexpected error occurred: {str(e)}"
        }

def check_image_status(job_id):
    endpoint = f"{API_BASE_URL}/api/v2/generate/check/{job_id}"

    try:
        response = requests.get(endpoint, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        debug(f"Status check response for job {job_id}: {json.dumps(data, indent=2)}")

        if 'done' in data and 'is_possible' in data:
            return {
                "success": True,
                **data
            }
        else:
            error(f"Unexpected response format for job {job_id}: {json.dumps(data, indent=2)}")
            return {
                "success": False,
                "message": data.get('message', 'Unknown error'),
                "statusCode": response.status_code
            }

    except requests.exceptions.RequestException as e:
        error(f"Error checking status for jobId: {job_id}. Details:\n{traceback.format_exc()}")
        return {
            "success": False,
            "statusCode": getattr(e.response, 'status_code', 0),
            "message": str(e)
        }
    except Exception as e:
        error(f"Unexpected error in check_image_status for job {job_id}: {str(e)}\nTraceback:\n{traceback.format_exc()}")
        return {
            "success": False,
            "statusCode": 500,
            "message": f"An unexpected error occurred: {str(e)}"
        }

def download_image(img_url):
    try:
        response = requests.get(img_url)
        response.raise_for_status()

        return {
            "success": True,
            "content": response.content
        }

    except requests.exceptions.RequestException as e:
        error(f"Error attempting to download image: {img_url}. {str(e)}")
        return {
            "success": False,
            "statusCode": getattr(e.response, 'status_code', 0),
            "message": "unknown error",
            "details": str(e)
        }

def retrieve_generated_image(job_id):
    endpoint = f"{API_BASE_URL}/api/v2/generate/status/{job_id}"

    try:
        response = requests.get(endpoint, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        debug(f"Image retrieval response for job {job_id}: {json.dumps(data, indent=2)}")

        if "generations" in data and data["generations"]:
            return data["generations"][0].get("img")
        else:
            error(f"No image URL found in the retrieval response for job {job_id}")
            return None

    except requests.exceptions.RequestException as e:
        error(f"Error: Unable to retrieve generated image for jobId: {job_id}. Details:\n{traceback.format_exc()}")
        return None