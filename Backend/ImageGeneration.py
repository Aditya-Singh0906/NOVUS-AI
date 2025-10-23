import asyncio
import os
from random import randint
from time import sleep
from Backend.Utils import resource_path

import requests
from PIL import Image
from dotenv import get_key
from Backend.Utils import resource_path
from dotenv import dotenv_values


# -------------------- CONFIG --------------------
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HUGGINGFACE_KEY = get_key(".env", "HuggingFaceAPIKey")

HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_KEY}"}
DATA_DIR = resource_path("Data")
IMAGE_FILE = resource_path(r"Frontend\Files\ImageGeneration.data")

env_path = resource_path(".env")
env_vars = dotenv_values(env_path)

# -------------------- HELPERS --------------------
def ensure_data_folder():
    """Create the Data folder if it doesn’t exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def open_images(prompt: str):
    """Open the saved images for a given prompt."""
    prompt = prompt.replace(" ", "_")
    files = [f"{prompt}{i}.jpg" for i in range(1, 5)]

    for jpg_file in files:
        image_path = os.path.join(DATA_DIR, jpg_file)
        try:
            img = Image.open(image_path)
            print(f"[INFO] Opening image: {image_path}")
            img.show()
            sleep(0.5)  # small delay so OS image viewer can catch up
        except IOError:
            print(f"[WARN] Unable to open {image_path}")


async def query(payload: dict) -> bytes:
    """Send a prompt to Hugging Face API with retries and return image bytes (or None if failed)."""
    for attempt in range(3):
        response = await asyncio.to_thread(
            requests.post, API_URL, headers=HEADERS, json=payload
        )
        if response.status_code == 200:
            return response.content
        print(f"[WARN] Attempt {attempt+1} failed: {response.text}")
        await asyncio.sleep(3)  # wait before retry
    return None



async def generate_images(prompt: str):
    """Generate 3 high-quality images for the given prompt."""
    ensure_data_folder()
    tasks = []

    for _ in range(3):
        payload = {
            "inputs": f"{prompt}, ultra realistic, cinematic lighting, "
                      f"8k resolution, high detail, sharp focus, "
                      f"seed={randint(0, 1_000_000)}"
        }
        tasks.append(asyncio.create_task(query(payload)))

    image_bytes_list = await asyncio.gather(*tasks)

    saved_files = []
    for i, image_bytes in enumerate(image_bytes_list, start=1):
        filename = os.path.join(DATA_DIR, f"{prompt.replace(' ', '_')}{i}.jpg")
        with open(filename, "wb") as f:
            f.write(image_bytes)
        saved_files.append(filename)
        print(f"[INFO] Saved: {filename}")

    return saved_files


def GenerateImages(prompt: str, open_after: bool = True):
    """Main wrapper: generate images and optionally open them."""
    print(f"[INFO] Generating images for prompt: {prompt}")
    try:
        files = asyncio.run(generate_images(prompt))
        if open_after:
            open_images(prompt)
        return files
    except Exception as e:
        print(f"[ERROR] Failed to generate images: {e}")
        return []


# -------------------- MONITOR LOOP (standalone mode) --------------------
def monitor_image_generation():
    """Continuously check the ImageGeneration.data file for requests."""
    while True:
        try:
            with open(IMAGE_FILE, "r") as f:
                Data = f.read().strip()

            if not Data:
                sleep(1)
                continue

            Prompt, Status = Data.split(",")

            if Status == "True":
                print("[INFO] Image request detected...")
                GenerateImages(prompt=Prompt)

                # reset the file
                with open(IMAGE_FILE, "w") as f:
                    f.write("False,False")
                break
            else:
                sleep(1)
        except Exception as e:
            print(f"[WARN] Monitor error: {e}")
            sleep(1)


if __name__ == "__main__":
    monitor_image_generation()
