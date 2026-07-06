import json

chat_examples = [
    {
        "input": "I'm feeling stressed about the upcoming project deadline.",
        "output": "It sounds like you're feeling overwhelmed. Let's talk about it—what specifically is stressing you out?",
    },
    {
        "input": "I had a really strange dream last night.",
        "output": "That sounds intriguing! Want to share more details about the dream?",
    },
    {
        "input": "I'm not sure if I made the right career decision.",
        "output": "It’s completely normal to have doubts. Let's explore what led you to that decision and how you're feeling about it now.",
    },
    {
        "input": "Do you think people still write letters nowadays?",
        "output": "Interesting question! Letter writing has definitely changed with technology. What are your thoughts on it?",
    },
    {
        "input": "I feel like I'm always falling behind on things.",
        "output": "That can feel really discouraging. Let's discuss what you feel is holding you back and see if we can break it down.",
    },
    {
        "input": "I just got back from a long trip and I feel exhausted.",
        "output": "Travel can be really draining. How was your trip, though? Anything exciting happen?",
    },
    {
        "input": "I’ve been thinking a lot about how social media impacts our lives.",
        "output": "That’s a deep topic. How do you feel social media has influenced your life personally?",
    },
    {
        "input": "Sometimes I don't feel like I'm good enough for the things I’m trying to do.",
        "output": "That’s a tough feeling to deal with. Want to dive deeper into where that’s coming from?",
    },
    {
        "input": "I was reading about productivity methods and it got me thinking about my own habits.",
        "output": "Productivity methods can be really insightful. Have you found any that resonate with you so far?",
    },
    {
        "input": "I wonder if animals experience emotions the way we do.",
        "output": "That’s a fascinating thought. There’s some interesting research on that—what’s your take on it?",
    },
]

user_intent_examples = [
    {
        "input": "I have to go to the grocery store and buy milk.",
        "output": json.dumps(
            [
                {
                    "name": "task_record",
                    "parameters": {
                        "tasks": [
                            {
                                "name": "Go to the grocery store",
                                "type": "task",
                                "task_size": "small",
                                "text": "Go to the grocery store",
                                "category": "shopping",
                                "priority": 1,
                                "sentiment": "neutral",
                                "due_date": None,
                            },
                            {
                                "type": "task",
                                "task_size": "small",
                                "text": "Buy milk",
                                "category": "shopping",
                                "priority": 1,
                                "sentiment": "neutral",
                                "due_date": None,
                            },
                        ],
                    },
                }
            ]
        ),
    },
    {
        "input": "Remind me to call mom tomorrow.",
        "output": json.dumps(
            [
                {
                    "name": "task_record",
                    "parameters": {
                        "tasks": [
                            {
                                "type": "task",
                                "task_size": "small",
                                "text": "Call mom",
                                "category": "personal_development",
                                "priority": 1,
                                "sentiment": "neutral",
                                "due_date": "2024-07-24",
                            }
                        ],
                    },
                }
            ]
        ),
    },
    {
        "input": "I have to go to the grocery store and buy milk, email my boss, and check my email for updates.",
        "output": json.dumps(
            [
                {
                    "name": "task_record",
                    "parameters": {
                        "tasks": [
                            {
                                "type": "task",
                                "task_size": "small",
                                "text": "Buy groceries",
                                "category": "shopping",
                                "priority": 1,
                                "sentiment": "neutral",
                                "due_date": None,
                            },
                            {
                                "type": "task",
                                "task_size": "small",
                                "text": "Finish report",
                                "category": "personal_development",
                                "priority": 1,
                                "sentiment": "neutral",
                                "due_date": "2024-07-24",
                            },
                        ],
                    },
                },
                {"name": "search_tasks", "parameters": {"keyword": "email"}},
            ]
        ),
    },
    {
        "input": "What do I need to do today?",
        "output": json.dumps([{"name": "search_tasks", "parameters": {"due_on": "2024-07-24"}}]),
    },
    {
        "input": "What tasks are due this week?",
        "output": json.dumps([{"name": "search_tasks", "parameters": {"due_before": "2024-07-31"}}]),
    },
    {
        "input": "What's the status of my report?",
        "output": json.dumps([{"name": "search_tasks", "parameters": {"keyword": "report"}}]),
    },
    {
        "input": "When is my dentist appointment?",
        "output": json.dumps([{"name": "search_tasks", "parameters": {"keyword": "dentist"}}]),
    },
    {
        "input": "Change the due date of my report to Friday.",
        "output": json.dumps(
            [{"name": "edit_task", "parameters": {"task_query": "report", "new_due_date": "2024-07-24"}}]
        ),
    },
    {
        "input": "Mark the groceries as done.",
        "output": json.dumps(
            [{"name": "edit_task", "parameters": {"task_query": "groceries", "new_status": "completed"}}]
        ),
    },
]
