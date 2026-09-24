# Seed script for Firestore "recipes" collection
from datetime import datetime, timezone
from google.cloud import firestore

# IMPORTANT: Hardcoded Project ID string
PROJECT_ID = "qwiklabs-gcp-03-5bec0b757af4"

SEEDED_RECIPES = [
    {
        "recipe_id": "creamy-garlic-chicken",
        "name": "Creamy Tuscan Garlic Chicken",
        "ingredients": ["chicken breast", "spinach", "garlic", "heavy cream", "sun-dried tomatoes", "olive oil", "parmesan"],
        "instructions": [
            "Season chicken breasts with salt and pepper.",
            "Sear chicken in olive oil over medium-high heat until golden, then set aside.",
            "Sauté minced garlic and sun-dried tomatoes in the same skillet.",
            "Pour in heavy cream and bring to a simmer.",
            "Stir in fresh spinach and parmesan cheese until spinach is wilted.",
            "Return chicken to the skillet and simmer for 5 minutes."
        ],
        "prep_time_mins": 25,
        "dietary_tags": ["low-carb", "gluten-free"],
        "is_favorite": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "recipe_id": "quick-veg-stirfry",
        "name": "Quick Vegetable Stir-Fry",
        "ingredients": ["bell pepper", "broccoli", "soy sauce", "garlic", "ginger", "sesame oil", "tofu"],
        "instructions": [
            "Cube tofu and press dry with paper towels.",
            "Heat sesame oil in a wok or large frying pan.",
            "Sear tofu cubes until crispy on all sides, then remove.",
            "Stir-fry broccoli florets and sliced bell peppers for 3-4 minutes.",
            "Add minced garlic, ginger, soy sauce, and return tofu to pan.",
            "Toss well for 1 minute and serve hot."
        ],
        "prep_time_mins": 15,
        "dietary_tags": ["vegan", "vegetarian"],
        "is_favorite": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "recipe_id": "garlic-herb-salmon",
        "name": "Garlic Herb Salmon & Asparagus",
        "ingredients": ["salmon fillet", "garlic", "butter", "lemon", "dill", "asparagus"],
        "instructions": [
            "Preheat oven to 400°F (200°C).",
            "Place salmon fillets and trimmed asparagus on a lined baking sheet.",
            "Melt butter and mix with minced garlic, chopped dill, and lemon juice.",
            "Drizzle garlic butter over salmon and asparagus.",
            "Bake for 12-15 minutes until salmon flakes easily with a fork."
        ],
        "prep_time_mins": 20,
        "dietary_tags": ["keto", "gluten-free", "pescatarian"],
        "is_favorite": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "recipe_id": "classic-tomato-basil-pasta",
        "name": "Classic Tomato Basil Pasta",
        "ingredients": ["penne pasta", "canned tomatoes", "garlic", "fresh basil", "olive oil", "parmesan"],
        "instructions": [
            "Boil penne pasta in salted water according to package directions.",
            "In a saucepan, warm olive oil and sauté sliced garlic until fragrant.",
            "Add crushed canned tomatoes and simmer for 10 minutes.",
            "Stir in torn fresh basil leaves and season with salt and pepper.",
            "Toss pasta with sauce and top with grated parmesan."
        ],
        "prep_time_mins": 20,
        "dietary_tags": ["vegetarian"],
        "is_favorite": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
]


def seed_database():
    print(f"Connecting to Firestore for project: '{PROJECT_ID}'...")
    import google.auth
    credentials, _ = google.auth.default()
    db = firestore.Client(project=PROJECT_ID, credentials=credentials)
    collection_ref = db.collection("recipes")

    for recipe in SEEDED_RECIPES:
        doc_ref = collection_ref.document(recipe["recipe_id"])
        doc_ref.set(recipe)
        print(f"✓ Seeded recipe: '{recipe['name']}' (ID: {recipe['recipe_id']})")

    print(f"\n🎉 Successfully seeded {len(SEEDED_RECIPES)} recipes into 'recipes' collection!")


if __name__ == "__main__":
    seed_database()
