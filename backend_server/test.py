test = {
    "the Ville": {
        "Oak Hill College": {
            "hallway": [],
            "library": ["library sofa", "library table", "bookshelf"],
            "classroom": [
                "blackboard",
                "classroom podium",
                "classroom student seating",
            ],
        },
    }
}
act_address = "the Ville:Oak Hill College:hallway"
curr_world, curr_sector, curr_area = act_address.split(":")
x = ", ".join(list(test[curr_world][curr_sector][curr_area]))
print("^", x, "^")
