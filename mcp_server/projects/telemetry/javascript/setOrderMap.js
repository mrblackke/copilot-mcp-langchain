function setOrderMap() {
    return {
        "": [
            "date",
            "total_active_users",
            "total_engaged_users",
            "copilot_ide_chat",
            "copilot_dotcom_chat",
            "copilot_dotcom_pull_requests",
            "copilot_ide_code_completions"
        ],
        "copilot_ide_chat": [
            "total_engaged_users",
            "editors"
        ],
        "copilot_ide_chat.editors": [
            "name",
            "total_engaged_users",
            "models"
        ],
        "copilot_ide_chat.editors.models": [
            "name",
            "is_custom_model",
            "custom_model_training_date",
            "total_chats",
            "total_engaged_users",
            "total_chat_copy_events",
            "total_chat_insertion_events"
        ],
        "copilot_dotcom_chat": [
            "total_engaged_users",
            "models"
        ],
        "copilot_dotcom_chat.models": [
            "name",
            "is_custom_model",
            "custom_model_training_date",
            "total_engaged_users",
            "total_chats"
        ],
        "copilot_dotcom_pull_requests": [
            "total_engaged_users",
            "repositories"
        ],
        "copilot_dotcom_pull_requests.repositories": [
            "name",
            "total_engaged_users",
            "models"
        ],
        "copilot_dotcom_pull_requests.repositories.models": [
            "name",
            "is_custom_model",
            "custom_model_training_date",
            "total_pr_summaries_created",
            "total_engaged_users"
        ],
        "copilot_ide_code_completions": [
            "total_engaged_users",
            "languages",
            "editors"
        ],
        "copilot_ide_code_completions.languages": [
            "name",
            "total_engaged_users"
        ],
        "copilot_ide_code_completions.editors": [
            "name",
            "total_engaged_users",
            "models"
        ],
        "copilot_ide_code_completions.editors.models": [
            "name",
            "is_custom_model",
            "custom_model_training_date",
            "total_engaged_users",
            "languages"
        ],
        "copilot_ide_code_completions.editors.models.languages": [
            "name",
            "total_engaged_users",
            "total_code_acceptances",
            "total_code_suggestions",
            "total_code_lines_accepted",
            "total_code_lines_suggested"
        ]
    };
}