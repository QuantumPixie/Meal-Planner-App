from dotenv import load_dotenv
from flask import Flask, render_template, jsonify
import json
import os
import requests

# Load environment variables from .env
load_dotenv()
spoonacular_api_key = os.environ.get('SPOONACULAR_API_KEY')

app = Flask(__name__)


def get_random_meal_plan():
    """
    This function uses the Spoonacular API to generate a random meal plan based on the user's dietary preferences and goals.

    Parameters:
        spoonacular_api_key (str): The API key for the Spoonacular API.
        target_calories (int): The target number of calories for the meal plan.
        time_frame (str): The time frame for the meal plan (e.g., "week" or "day").

    Returns:
        dict: A dictionary containing the meal plan for the specified time frame.

    """
    spoonacular_endpoint = 'https://api.spoonacular.com/mealplanner/generate'
    params = {
        'apiKey': spoonacular_api_key,
        'targetCalories': 2000,
        'timeFrame': 'week',
    }

    response = requests.get(spoonacular_endpoint, params=params)
    data = response.json()

    return data['week']

def save_to_json(meal_plan, filename='random_meal_plan.json'):
    """
    Save a meal plan to a JSON file.

    Args:
        meal_plan (dict): The meal plan to save.
        filename (str, optional): The filename to save the meal plan to. Defaults to 'custom_meal_plan.json'.
    """
    with open(filename, 'w') as file:
        json.dump(meal_plan, file, indent=2)

# PROGRAM START
# First check for saved file:
try:
    with open('random_meal_plan.json', 'r') as file:
        weekly_meal_plan = json.load(file)
except FileNotFoundError:
    weekly_meal_plan = None

# Generate the random meal plan if file doesn't exist
if weekly_meal_plan == None:
    weekly_meal_plan = get_random_meal_plan()
    # Save the random meal plan to file
    save_to_json(weekly_meal_plan, filename='random_meal_plan.json')

def add_to_custom_meal_plan_json(day, meal_info, filename='custom_meal_plan.json'):
    """
    Add a meal to a custom meal plan.

    Args:
        day (str): The day of the week (e.g., "Sunday").
        meal_info (dict): The information about the meal to add, including its title, ID, ready in minutes, servings, and URL.
        filename (str, optional): The filename of the custom meal plan. Defaults to 'custom_meal_plan.json'.
    """
    try:
        with open(filename, 'r') as file:
            custom_meal_plan = json.load(file)
    except FileNotFoundError:
        custom_meal_plan = {}

    if day not in custom_meal_plan:
        custom_meal_plan[day] = []

    custom_meal_plan[day].append({
        'title': meal_info['title'],
        'id': meal_info['id'],
        'readyInMinutes': meal_info['readyInMinutes'],
        'servings': meal_info['servings'],
        'url': meal_info['sourceUrl'],
    })

    save_to_json(custom_meal_plan, filename)
    with open(filename, 'w') as file:
        json.dump(custom_meal_plan, file, indent=2)

@app.route('/')
def index():
    """
    This function uses the Spoonacular API to generate a random meal plan based on the user's dietary preferences and goals.

    Parameters:
        spoonacular_api_key (str): The API key for the Spoonacular API.
        target_calories (int): The target number of calories for the meal plan.
        time_frame (str): The time frame for the meal plan (e.g., "week" or "day").

    Returns:
        dict: A dictionary containing the meal plan for the specified time frame.

    """
    # Extract only the recipe title and ID for each day
    meals_by_day = {
        day: [{
            'id': meal['id'],
            'readyInMinutes': meal['readyInMinutes'],
            'servings': meal['servings'],
            'title': meal['title'],
        } for meal in meals['meals']]
        for day, meals in weekly_meal_plan.items()
    }

    # Render meal plan to template
    return render_template('index.html', meals_by_day=meals_by_day)


@app.route('/view_recipe/<int:recipe_id>')
def get_recipe(recipe_id):
    """
    Get information about a recipe using the Spoonacular API.

    Args:
        recipe_id (int): The ID of the recipe.

    Returns:
        dict: The information about the recipe.

    """
    url = f'https://api.spoonacular.com/recipes/{recipe_id}/information'
    params = {
        'apiKey': spoonacular_api_key,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        recipe = response.json()
        return render_template('view_recipe.html', recipe=recipe)

    except requests.RequestException as e:
        # Handle any exception that occurred during the request
        return f"Error: {str(e)}", 500  # Return a generic error message with a 500 status code
    except json.JSONDecodeError as e:
        # Handle JSON decoding errors
        return f"Error decoding JSON: {str(e)}", 500
    
@app.route('/custom_meal_plan')
def custom_meal_plan():
    
    try:
        with open('custom_meal_plan.json', 'r') as file:
            all_meal_plans = json.load(file)
    except FileNotFoundError:
        all_meal_plans = {}

    return render_template('custom_meal_plan.html', all_meal_plans=all_meal_plans)

@app.route('/add_to_custom_meal_plan/<string:day>/<string:meal_id>')
def add_to_custom_meal_plan(day, meal_id):
    """
    Render the 'custom_meal_plan.html' template with custom meal plans.

    Attempts to read custom meal plans from 'custom_meal_plan.json'. If the file
    is not found, an empty dictionary is used. The function then renders the
    'custom_meal_plan.html' template, passing the custom meal plans as a context
    variable.

    Returns:
        Flask Response: Rendered HTML template displaying custom meal plans.
    """
    meal_info = find_meal_info(meal_id)

    if not meal_info:
        return jsonify({'message': 'Meal not found in meal plan'}), 404

    try:
        add_to_custom_meal_plan_json(day, meal_info)
        return jsonify({'message': 'Meal added to custom meal plan'})
    except Exception as e:
        return jsonify({'message': f'Error adding meal to custom meal plan: {str(e)}'}), 500

@app.route('/display_custom_meal_plan')
def display_custom_meal_plan():
    """
    Display the custom meal plans stored in 'custom_meal_plan.json' on the webpage.

    This function attempts to read the custom meal plans from a JSON file and renders
    the 'custom_meal_plan.html' template, passing the meal plans as a context variable.

    Returns:
        Flask Response: Rendered HTML template displaying custom meal plans.
    """
    try:
        with open('custom_meal_plan.json', 'r') as file:
            custom_meal_plan = json.load(file)
    except FileNotFoundError:
        custom_meal_plan = {}

    return render_template('display_custom_meal_plan.html', custom_meal_plan=custom_meal_plan)

def find_meal_info(meal_id):
    """
    Find the meal information for a given meal ID.

    Args:
        meal_id (str): The ID of the meal.

    Returns:
        Optional[dict]: The meal information, or None if the meal was not found.
    """
    for day in weekly_meal_plan.keys():
        for meal in weekly_meal_plan[day]['meals']:
            if int(meal['id']) == int(meal_id):
                return meal
    return None

if __name__ == '__main__':
    app.run(debug=True)




# TODO:

# Generate a shopping list based on the selected custom meal plan
# Refresh Mealplanner if meals are not enjoyed
# Remove Meals from the Custom Meal Plan
# Automate sending the Meal Plan including the shopping list to the inbox
   
