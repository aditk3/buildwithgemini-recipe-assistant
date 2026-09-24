# Firestore Tools for Recipe Assistant Agent
from datetime import datetime, timezone
import json
import os
import re
import urllib.parse
import urllib.request
from google import genai
from google.adk.tools import ToolContext
from google.genai import types
from google.cloud import firestore, storage

# IMPORTANT: Hardcoded Project ID string as required for Agent Platform
PROJECT_ID = "qwiklabs-gcp-03-5bec0b757af4"
BUCKET_NAME = "recipe-assistant-media-qwiklabs-gcp-03-5bec0b757af4"

# Initialize Firestore client with explicit project ID string
db = firestore.Client(project=PROJECT_ID)
recipes_col = db.collection("recipes")


def search_recipes(ingredients: str = "", max_prep_time: int = 0, dietary_tag: str = "") -> str:
    """
    Search recipes in the Firestore database matching available ingredients, max preparation time, or dietary preferences.

    Args:
        ingredients: Comma-separated list of ingredients available on hand (e.g. "chicken, garlic, spinach").
        max_prep_time: Maximum preparation time in minutes (0 for no limit).
        dietary_tag: Optional dietary tag to filter by (e.g. "vegan", "gluten-free", "low-carb", "keto").

    Returns:
        Formatted summary string of matching recipes found in Firestore.
    """
    try:
        docs = recipes_col.stream()
        matched = []
        user_ingredients = [i.strip().lower() for i in ingredients.split(",") if i.strip()]
        user_tag = dietary_tag.strip().lower() if dietary_tag else ""

        for doc in docs:
            data = doc.to_dict()
            rec_ingredients = [i.lower() for i in data.get("ingredients", [])]
            rec_prep_time = data.get("prep_time_mins", 0)
            rec_tags = [t.lower() for t in data.get("dietary_tags", [])] if isinstance(data.get("dietary_tags"), list) else []

            # Check max prep time filter
            if max_prep_time > 0 and rec_prep_time > max_prep_time:
                continue

            # Check dietary tag filter
            if user_tag and user_tag not in rec_tags:
                continue

            # Check ingredient match score
            matching_count = 0
            if user_ingredients:
                for ui in user_ingredients:
                    if any(ui in ri for ri in rec_ingredients):
                        matching_count += 1

            matched.append({
                "recipe_id": doc.id,
                "name": data.get("name"),
                "ingredients": data.get("ingredients", []),
                "instructions": data.get("instructions", []),
                "prep_time_mins": rec_prep_time,
                "dietary_tags": data.get("dietary_tags", []),
                "is_favorite": data.get("is_favorite", False),
                "match_score": matching_count
            })

        # Sort by ingredient match score (descending)
        if user_ingredients:
            matched.sort(key=lambda x: x["match_score"], reverse=True)

        if not matched:
            return "No recipes found matching your criteria in Firestore."

        output = [f"Found {len(matched)} recipe(s) in Firestore:\n"]
        for r in matched:
            fav_star = "⭐ " if r["is_favorite"] else ""
            output.append(f"• {fav_star}{r['name']} ({r['prep_time_mins']} mins) [ID: {r['recipe_id']}]")
            output.append(f"  Ingredients: {', '.join(r['ingredients'])}")
            output.append(f"  Tags: {', '.join(r['dietary_tags']) if r['dietary_tags'] else 'None'}")
            output.append(f"  Steps: {' -> '.join(r['instructions'][:2])}...\n")

        return "\n".join(output)
    except Exception as e:
        return f"Error searching Firestore recipes: {str(e)}"


def get_favorite_recipes() -> str:
    """
    Retrieve all favorite recipes saved in the Firestore database.

    Returns:
        Formatted summary of saved favorite recipes.
    """
    try:
        query = recipes_col.where("is_favorite", "==", True).stream()
        favorites = []
        for doc in query:
            data = doc.to_dict()
            favorites.append(data)

        if not favorites:
            return "No favorite recipes saved in Firestore yet."

        output = [f"⭐ Saved Favorite Recipes ({len(favorites)}):\n"]
        for data in favorites:
            output.append(f"• {data.get('name')} ({data.get('prep_time_mins', 20)} mins)")
            output.append(f"  Ingredients: {', '.join(data.get('ingredients', []))}")
            output.append(f"  Instructions:")
            for idx, step in enumerate(data.get("instructions", []), 1):
                output.append(f"    {idx}. {step}")
            output.append("")

        return "\n".join(output)
    except Exception as e:
        return f"Error fetching favorite recipes from Firestore: {str(e)}"


def save_recipe(
    name: str,
    ingredients: list[str],
    instructions: list[str],
    prep_time_mins: int = 20,
    dietary_tags: list[str] = None,
    is_favorite: bool = True
) -> str:
    """
    Save or add a new recipe to the Firestore database.

    Args:
        name: Name of the recipe (e.g. "Lemon Garlic Butter Shrimp").
        ingredients: List of ingredient strings.
        instructions: List of step-by-step instruction strings.
        prep_time_mins: Estimated preparation time in minutes.
        dietary_tags: Optional list of dietary tags (e.g. ["gluten-free", "keto"]).
        is_favorite: Whether to mark this recipe as a favorite (default: True).

    Returns:
        Confirmation message with the Firestore document ID.
    """
    try:
        recipe_id = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        doc_ref = recipes_col.document(recipe_id)

        recipe_data = {
            "recipe_id": recipe_id,
            "name": name,
            "ingredients": ingredients,
            "instructions": instructions,
            "prep_time_mins": prep_time_mins,
            "dietary_tags": dietary_tags or [],
            "is_favorite": is_favorite,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        doc_ref.set(recipe_data, merge=True)
        fav_msg = " marked as favorite" if is_favorite else ""
        return f"Successfully saved recipe '{name}' (ID: {recipe_id}) to Firestore{fav_msg}!"
    except Exception as e:
        return f"Error saving recipe to Firestore: {str(e)}"


def toggle_favorite_recipe(recipe_name_or_id: str, is_favorite: bool = True) -> str:
    """
    Toggle or update the favorite status of a recipe in Firestore.

    Args:
        recipe_name_or_id: Name or document ID of the recipe.
        is_favorite: True to mark as favorite, False to remove from favorites.

    Returns:
        Confirmation message.
    """
    try:
        recipe_id = re.sub(r'[^a-z0-9]+', '-', recipe_name_or_id.lower()).strip('-')
        doc_ref = recipes_col.document(recipe_id)
        doc = doc_ref.get()

        if not doc.exists:
            # Try searching by exact or partial name
            docs = recipes_col.stream()
            found_doc = None
            for d in docs:
                if d.to_dict().get("name", "").lower() == recipe_name_or_id.lower():
                    found_doc = d
                    break
            if found_doc:
                doc_ref = recipes_col.document(found_doc.id)
            else:
                return f"Recipe '{recipe_name_or_id}' not found in Firestore database."

        doc_ref.update({"is_favorite": is_favorite, "updated_at": datetime.now(timezone.utc).isoformat()})
        status_text = "added to" if is_favorite else "removed from"
        return f"Recipe '{recipe_name_or_id}' has been {status_text} favorites in Firestore!"
    except Exception as e:
        return f"Error updating favorite status in Firestore: {str(e)}"


def get_all_recipes() -> str:
    """
    Retrieve all recipes stored in the Firestore database.

    Returns:
        Formatted summary string of all recipes.
    """
    try:
        docs = recipes_col.stream()
        recipes = [doc.to_dict() for doc in docs]

        if not recipes:
            return "No recipes found in Firestore database."

        output = [f"📖 All Recipes in Firestore ({len(recipes)}):\n"]
        for r in recipes:
            fav = "⭐ " if r.get("is_favorite") else ""
            output.append(f"• {fav}{r.get('name')} ({r.get('prep_time_mins', 20)} mins) [ID: {r.get('recipe_id')}]")
            output.append(f"  Ingredients: {', '.join(r.get('ingredients', []))}")
            output.append(f"  Tags: {', '.join(r.get('dietary_tags', [])) if r.get('dietary_tags') else 'None'}\n")

        return "\n".join(output)
    except Exception as e:
        return f"Error fetching all recipes from Firestore: {str(e)}"


def export_recipe_to_gcs(recipe_id: str) -> str:
    """
    Export a recipe from Firestore to a public Cloud Storage bucket as a shareable Markdown file.

    Args:
        recipe_id: Document ID of the recipe to export (e.g. "creamy-garlic-chicken").

    Returns:
        Public HTTPS URL to view or download the exported recipe card.
    """
    try:
        clean_id = recipe_id.lower().strip()
        doc_ref = recipes_col.document(clean_id)
        doc = doc_ref.get()
        if not doc.exists:
            return f"Recipe '{clean_id}' not found in Firestore."

        data = doc.to_dict()
        name = data.get("name", clean_id)
        ingredients = data.get("ingredients", [])
        instructions = data.get("instructions", [])
        prep_time = data.get("prep_time_mins", 20)
        tags = data.get("dietary_tags", [])

        md_content = f"# 🍳 {name}\n\n"
        md_content += f"**Prep Time:** {prep_time} minutes  \n"
        md_content += f"**Dietary Tags:** {', '.join(tags) if tags else 'None'}\n\n"
        md_content += "## 🛒 Ingredients\n"
        for ing in ingredients:
            md_content += f"- {ing}\n"
        md_content += "\n## 👩‍🍳 Instructions\n"
        for idx, step in enumerate(instructions, 1):
            md_content += f"{idx}. {step}\n"

        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"recipes/{clean_id}.md")
        blob.upload_from_string(md_content, content_type="text/markdown")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/recipes/{clean_id}.md"
        return f"Recipe '{name}' exported successfully! View shareable card at: {public_url}"
    except Exception as e:
        return f"Error exporting recipe to Cloud Storage: {str(e)}"


def fetch_online_recipes(query: str) -> str:
    """
    Search TheMealDB public API for real-world online recipes matching a query.

    Args:
        query: Recipe or dish name to search online (e.g. "pasta", "chicken", "tacos").

    Returns:
        Formatted summary of matching online recipes including ingredients and instructions.
    """
    api_key = os.getenv("THEMEALDB_API_KEY", "1")
    encoded_query = urllib.parse.quote(query.strip())
    url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded_query}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RecipeAssistant/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        meals = data.get("meals")
        if not meals:
            return f"No online recipes found matching '{query}' on TheMealDB."

        output = [f"🌐 Found {len(meals[:3])} online recipe(s) for '{query}':\n"]
        for meal in meals[:3]:
            name = meal.get("strMeal")
            category = meal.get("strCategory")
            area = meal.get("strArea")
            instructions = meal.get("strInstructions", "").strip()
            image_url = meal.get("strMealThumb")

            ingredients = []
            for i in range(1, 21):
                ing = meal.get(f"strIngredient{i}")
                meas = meal.get(f"strMeasure{i}")
                if ing and ing.strip():
                    measure_str = f" ({meas.strip()})" if meas and meas.strip() else ""
                    ingredients.append(f"{ing.strip()}{measure_str}")

            output.append(f"• 🍲 {name} ({category} / {area})")
            output.append(f"  Ingredients: {', '.join(ingredients[:8])}")
            if image_url:
                output.append(f"  Image: {image_url}")
            output.append(f"  Instructions: {instructions[:180]}...\n")

        return "\n".join(output)
    except Exception as e:
        return f"Error fetching online recipes from TheMealDB: {str(e)}"


def generate_recipe_image(dish_name: str, tool_context: ToolContext) -> str:
    """
    Generate an image for a recipe or dish using gemini-3.1-flash-lite-image in location 'global',
    save it as an ADK artifact for the Playground, and upload the image bytes to public Cloud Storage.

    Args:
        dish_name: Name or description of the recipe/dish to generate an image for (e.g., "Tuscan Garlic Chicken").
        tool_context: ADK ToolContext injected automatically by the framework.

    Returns:
        Public HTTPS URL of the generated image hosted on Cloud Storage.
    """
    try:
        genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global"
        )

        prompt = f"A high-quality, delicious food photograph of {dish_name}, professionally plated, warm restaurant lighting."

        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            )
        )

        if not response.candidates or not response.candidates[0].content.parts:
            return f"No image generated for '{dish_name}'."

        part = response.candidates[0].content.parts[0]
        image_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type or "image/jpeg"

        clean_name = re.sub(r'[^a-z0-9]+', '_', dish_name.lower()).strip('_')
        ext = "png" if "png" in mime_type else "jpg"
        filename = f"{clean_name}.{ext}"

        # 1. Save artifact in ToolContext for ADK Playground
        tool_context.save_artifact(filename=filename, artifact=part)

        # 2. Upload image bytes directly to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_path = f"images/{filename}"
        blob = bucket.blob(blob_path)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"
        return f"Successfully generated image for '{dish_name}'!\nPublic Image URL: {public_url}"
    except Exception as e:
        return f"Error generating dish image: {str(e)}"




