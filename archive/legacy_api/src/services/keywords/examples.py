import json

examples = [
    {
        "query": "Buy groceries for the week",
        "keywords": json.dumps(
            ["shopping", "food", "meal prep", "ingredients", "supplies", "essentials", "produce"]
        ),
    },
    {
        "query": "Schedule a meeting with the design team",
        "keywords": json.dumps(
            [
                "appointment",
                "collaboration",
                "discussion",
                "conference",
                "planning",
                "creative session",
            ]
        ),
    },
    {
        "query": "Pick up dry cleaning after work",
        "keywords": json.dumps(
            ["laundry", "clothes", "garments", "cleaning service", "collection", "personal items"]
        ),
    },
    {
        "query": "Call mom to check on her",
        "keywords": json.dumps(
            ["family", "well-being", "conversation", "catch up", "care", "personal connection"]
        ),
    },
    {
        "query": "Finish the report by end of day",
        "keywords": json.dumps(
            ["document", "deadline", "submission", "work", "task", "completion", "progress"]
        ),
    },
    {
        "query": "Book a flight to San Francisco",
        "keywords": json.dumps(["travel", "airfare", "trip", "itinerary", "destination", "reservation"]),
    },
    {
        "query": "Plan a birthday party for John",
        "keywords": json.dumps(
            ["celebration", "event", "preparation", "gathering", "invitees", "festivities"]
        ),
    },
    {
        "query": "Water the plants in the living room",
        "keywords": json.dumps(["care", "gardening", "maintenance", "houseplants", "nurture", "hydration"]),
    },
    {
        "query": "Renew car insurance before it expires",
        "keywords": json.dumps(["policy", "coverage", "automobile", "renewal", "protection", "deadline"]),
    },
    {
        "query": "Prepare for the presentation tomorrow",
        "keywords": json.dumps(
            ["slides", "talk", "meeting", "speech", "public speaking", "practice", "event"]
        ),
    },
    {
        "query": "Make an appointment with the dentist",
        "keywords": json.dumps(["health", "checkup", "oral care", "consultation", "routine visit", "care"]),
    },
    {
        "query": "Organize files on my computer",
        "keywords": json.dumps(
            ["cleanup", "folders", "data management", "system", "documents", "digital organization"]
        ),
    },
    {
        "query": "Take out the trash on Monday",
        "keywords": json.dumps(["waste", "disposal", "cleanup", "routine", "sanitation", "chores"]),
    },
    {
        "query": "Send the invoice to the client",
        "keywords": json.dumps(["billing", "payment", "business", "transaction", "document", "finance"]),
    },
    {
        "query": "Walk the dog in the park",
        "keywords": json.dumps(
            ["exercise", "pet care", "outdoors", "routine", "companionship", "physical activity"]
        ),
    },
    {
        "query": "Reply to the project email",
        "keywords": json.dumps(["communication", "response", "work", "update", "message", "collaboration"]),
    },
    {
        "query": "Update my resume for job applications",
        "keywords": json.dumps(["career", "document", "professional", "CV", "job search", "revisions"]),
    },
    {
        "query": "Pick up the kids from school",
        "keywords": json.dumps(["family", "transportation", "care", "routine", "schedule", "responsibility"]),
    },
    {
        "query": "Cook dinner for the family tonight",
        "keywords": json.dumps(["meal preparation", "cuisine", "food", "household", "cooking", "evening"]),
    },
    {
        "query": "Write a thank you note to the team",
        "keywords": json.dumps(
            ["appreciation", "message", "acknowledgment", "gratitude", "communication", "workplace"]
        ),
    },
]
