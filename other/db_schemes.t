# user profile database scheme

{
    "_id": ObjectId(''),
    "user_id": int,
    "username": "",
    "stats": {
        "points": int,
        "rank": "",
        "completions": {
            "1-50": int,
            "51-100": int,
            "101-150": int,
            "151-199": int,
            "200": int
        }
    }
}
