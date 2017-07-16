def format_text(recipient_id, text):
    return {
        "recipient": {"id": recipient_id},
        "message": {
            "text": text,
        }
    }


def format_quick_replies(recipient_id, quick_replies, button_text='?'):
    return {
        "recipient": {"id": recipient_id},
        "message": {
            "text": button_text,
            "quick_replies": quick_replies
        }
    }


def format_button(recipient_id, button_text, buttons):
    """ Ref: https://developers.facebook.com/docs/messenger-platform/send-api-reference/button-template """
    return {
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": button_text,
                    "buttons": buttons,
                }
            }
        }
    }


def format_image_attachment(recipient_id, url):
    return {
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "image",
                "payload": {
                    "url": url
                }
            }
        }
    }