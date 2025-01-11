from app.main import *
from flask import Blueprint, jsonify, request
from db_handler import TaskType, SchedulerState


bp = Blueprint("ailert", __name__, url_prefix="/internal/v1")


@bp.route('/start-scheduler/<task_type>', methods=['POST'])
def start_scheduler(task_type):
    if task_type not in [t.value for t in TaskType]:
        return jsonify({
            "status": "error",
            "message": "Invalid task type. Use 'daily' or 'weekly'"
        }), 400

    if scheduler_state["is_running"]:
        return jsonify({
            "status": "error",
            "message": "Scheduler is already running"
        }), 400

    stop_event.clear()
    scheduler_state["is_running"] = True
    scheduler_state["is_paused"] = False
    scheduler_state["task_type"] = task_type

    scheduler_thread.start()

    return jsonify({
        "status": "success",
        "message": f"{task_type} scheduler started successfully",
        "state": SchedulerState.RUNNING.value
    })


@bp.route('/manage-scheduler/<action>', methods=['POST'])
def manage_scheduler(action):
    if not scheduler_state["is_running"]:
        return jsonify({
            "status": "error",
            "message": "No scheduler is currently running"
        }), 400

    if action == "pause":
        if scheduler_state["is_paused"]:
            return jsonify({
                "status": "error",
                "message": "Scheduler is already paused"
            }), 400
        scheduler_state["is_paused"] = True
        state = SchedulerState.PAUSED.value
        message = "Scheduler paused successfully"

    elif action == "resume":
        if not scheduler_state["is_paused"]:
            return jsonify({
                "status": "error",
                "message": "Scheduler is not paused"
            }), 400
        scheduler_state["is_paused"] = False
        state = SchedulerState.RUNNING.value
        message = "Scheduler resumed successfully"

    elif action == "stop":
        stop_event.set()
        if scheduler_thread:
            scheduler_thread.join()
        schedule.clear()
        scheduler_state["task_type"] = None
        state = SchedulerState.STOPPED.value
        message = "Scheduler stopped successfully"

    else:
        return jsonify({
            "status": "error",
            "message": "Invalid action. Use 'pause', 'resume', or 'stop'"
        }), 400

    return jsonify({
        "status": "success",
        "message": message,
        "state": state,
        "task_type": scheduler_state["task_type"]
    })


@bp.route('/scheduler-status', methods=['GET'])
def get_scheduler_status():
    if not scheduler_state["is_running"]:
        state = SchedulerState.STOPPED.value
    elif scheduler_state["is_paused"]:
        state = SchedulerState.PAUSED.value
    else:
        state = SchedulerState.RUNNING.value

    return jsonify({
        "is_running": scheduler_state["is_running"],
        "state": state,
        "task_type": scheduler_state["task_type"]
    })


@bp.route('/generate-newsletter', methods=['POST'])
async def api_generate_newsletter():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided",
                "timestamp": utility.get_formatted_timestamp()
            }), 400

        sections = data.get('sections')
        task_type = data.get('task_type')

        if not sections or not task_type:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: sections or task_type",
                "timestamp": utility.get_formatted_timestamp()
            }), 400

        if task_type not in [TaskType.WEEKLY.value, TaskType.DAILY.value]:
            return jsonify({
                "status": "error",
                "message": f"Invalid task_type. Must be either 'weekly' or 'daily'",
                "timestamp": utility.get_formatted_timestamp()
            }), 400

        newsletter_html = await generate_newsletter(sections, task_type)

        return jsonify({
            "status": "success",
            "message": "Newsletter generated successfully",
            "content": newsletter_html,
            "timestamp": utility.get_formatted_timestamp()
        })

    except Exception as e:
        logging.error(f"Error generating newsletter: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error generating newsletter: {str(e)}",
            "timestamp": utility.get_formatted_timestamp()
        }), 500


@bp.route('/save-newsletter', methods=['POST'])
def api_save_newsletter():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided",
                "timestamp": utility.get_formatted_timestamp()
            }), 400

        content = data.get('content')
        content_type = data.get('content_type')

        if not content or not content_type:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: content or content_type",
                "timestamp": utility.get_formatted_timestamp()
            }), 400

        if content_type not in ['weekly', 'daily']:
            return jsonify({
                "status": "error",
                "message": "Invalid content_type. Must be either 'weekly' or 'daily'",
                "timestamp": utility.get_formatted_timestamp()
            }), 400

        saved_item = save_to_db(content, content_type)

        return jsonify({
            "status": "success",
            "message": "Newsletter saved successfully",
            "newsletterId": saved_item["newsletterId"],
            "timestamp": utility.get_formatted_timestamp()
        })

    except Exception as e:
        logging.error(f"Error saving newsletter: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error saving newsletter: {str(e)}",
            "timestamp": utility.get_formatted_timestamp()
        }), 500


@bp.route('/send-email', methods=['POST'])
async def api_send_email():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided",
                "timestamp": utility.get_formatted_timestamp()
            }), 400

        recipients = data.get('recipients', [])
        content = data.get('content')
        template_id = data.get('template_id')

        if not content:
            return jsonify({
                "status": "error",
                "message": "Missing required field: content",
                "timestamp": utility.get_formatted_timestamp()
            }), 400

        result = await send_email(recipients, content, template_id)

        return jsonify({
            **result,  # Include all fields from the EmailService response
            "timestamp": utility.get_formatted_timestamp()
        })

    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error sending email: {str(e)}",
            "timestamp": utility.get_formatted_timestamp()
        }), 500


@bp.route('/generate-and-send', methods=['POST'])
async def api_generate_and_send():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided",
                "timestamp": utility.get_formatted_timestamp()
            }), 400

        sections = data.get('sections')
        task_type = data.get('task_type')
        recipients = data.get('recipients', [])

        if not sections or not task_type:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: sections or task_type",
                "timestamp": utility.get_formatted_timestamp()
            }), 400

        # Generate newsletter
        newsletter_html = await generate_newsletter(sections, task_type)

        # Save to database
        saved_item = save_to_db(newsletter_html, task_type)

        # Send email
        email_result = await send_email(recipients, saved_item["content"], saved_item["newsletterId"])

        return jsonify({
            "status": "success",
            "message": "Newsletter generated and sent successfully",
            "newsletterId": saved_item["newsletterId"],
            "email_status": email_result,
            "timestamp": utility.get_formatted_timestamp()
        })

    except Exception as e:
        logging.error(f"Error in generate and send workflow: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error in generate and send workflow: {str(e)}",
            "timestamp": utility.get_formatted_timestamp()
        }), 500