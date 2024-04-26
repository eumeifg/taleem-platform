db = db.getSiblingDB('edxapp')

db.createUser(
    {
        user: "edxapp",
        pwd: "BKOCTmy6c9Kdx4NwrGKcYIIsieZj6FcnHPr",
        roles:[
            {
                role: "readWrite",
                db:   "edxapp"
            }
        ]
    }
);