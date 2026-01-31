def send_notification(user_id, message, timestamp, channel, priority):
    notification_payload = {"user_id": user_id, "message": message, "timestamp": timestamp, "channel": channel, "priority": priority}
    return notification_payload
