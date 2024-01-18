// script.js
function add_to_custom_meal_plan(day, mealTitle) {
    fetch(`/add_to_custom_meal_plan/${day}/${mealTitle}`)
        .then(response => response.json())
        .then(data => {
            alert(data.message);
        })
        .catch(error => console.error('Error:', error));
}