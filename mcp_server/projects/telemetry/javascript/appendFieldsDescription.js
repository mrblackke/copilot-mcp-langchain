/**
 * Appends GitHub Copilot telemetry fields descriptions to the data.
 * 
 * @param {Object} params - Parameters object
 * @param {Array} params.data - The telemetry data array
 * @returns {Array} Data with descriptions added as first element
 */
function appendFieldsDescription(params) {
    const data = params.data;
    
    let result;
    if (!Array.isArray(data)) {
        result = [data];
    } else {
        result = [...data];
    }
    // Add descriptions as first element
    const descriptions = {
        "date": "The date for which the usage metrics are aggregated, in YYYY-MM-DD format.",
        "total_active_users": "The total number of Copilot users with activity belonging to any Copilot feature, globally, for the given day.",
        "total_engaged_users": "The total number of Copilot users who engaged with any Copilot feature, for the given day.",
        "copilot_ide_chat": {
            "total_engaged_users": "Total number of users who prompted Copilot Chat in the IDE.",
            "editors": [{
                "name": "Name of the given editor.",
                "total_engaged_users": "The number of users who prompted Copilot Chat in the specified editor.",
                "models": [{
                    "name": "Name of the model used for Copilot Chat.",
                    "is_custom_model": "Indicates whether a model is custom or default.",
                    "custom_model_training_date": "The training date for the custom model.",
                    "total_chats": "The total number of chats initiated by users.",
                    "total_engaged_users": "The number of users who prompted Copilot Chat.",
                    "total_chat_copy_events": "The number of times users copied code suggestions.",
                    "total_chat_insertion_events": "The number of times users accepted code suggestions."
                }]
            }]
        },
        "copilot_dotcom_chat": {
            "total_engaged_users": "Total number of users who prompted Copilot Chat on github.com.",
            "models": [{
                "name": "Name of the model used for Copilot Chat.",
                "is_custom_model": "Indicates whether a model is custom or default.",
                "custom_model_training_date": "The training date for the custom model.",
                "total_engaged_users": "Total number of users who prompted Copilot Chat on github.com.",
                "total_chats": "Total number of chats initiated by users on github.com."
            }]
        },
        "copilot_dotcom_pull_requests": {
            "total_engaged_users": "The number of users who used Copilot for Pull Requests.",
            "repositories": [{
                "name": "Repository name",
                "total_engaged_users": "The number of users who generated pull request summaries.",
                "models": [{
                    "name": "Name of the model used for Copilot pull request summaries.",
                    "is_custom_model": "Indicates whether a model is custom or default.",
                    "custom_model_training_date": "The training date for the custom model.",
                    "total_pr_summaries_created": "The number of pull request summaries generated.",
                    "total_engaged_users": "The number of users who generated pull request summaries."
                }]
            }]
        },
        "copilot_ide_code_completions": {
            "total_engaged_users": "Number of users who accepted at least one Copilot code completion suggestion.",
            "languages": [{
                "name": "Code completion metrics for active languages.",
                "total_engaged_users": "Number of users who accepted code completion suggestions for this language."
            }],
            "editors": [{
                "name": "Name of the editor used for Copilot code completion suggestions.",
                "total_engaged_users": "Number of users who accepted code completion suggestions in this editor.",
                "models": [{
                    "name": "Name of the model used for Copilot code completion suggestions.",
                    "is_custom_model": "Indicates whether a model is custom or default.",
                    "custom_model_training_date": "The training date for the custom model.",
                    "total_engaged_users": "Number of users who accepted code completion suggestions for this model.",
                    "languages": [{
                        "name": "Name of the language used for Copilot code completion suggestions.",
                        "total_engaged_users": "Number of users who accepted code completion suggestions for this language.",
                        "total_code_acceptances": "The number of Copilot code suggestions accepted.",
                        "total_code_suggestions": "The number of Copilot code suggestions generated.",
                        "total_code_lines_accepted": "The number of lines of code accepted from suggestions.",
                        "total_code_lines_suggested": "The number of lines of code suggested."
                    }]
                }]
            }]
        }
    };
    
    result.unshift(descriptions);
    // Возвращаем массив объектов, не сериализуем в строку
    return result;
}