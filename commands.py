from datetime import timedelta
import time
import data  # data.check_rate_limits, data.record_api_call, data.add_notification, data.generate_readable_timestamp

CYCLE_TIMES = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
    "monthly": timedelta(days=30),
}

def process_comment_command(comment_author, command_parts):
    command = command_parts[0].lower().lstrip("!")
    sender = data.fix_name(comment_author)

    if command == "s":
        if len(command_parts) != 3:
            return "Failed to send. Check recipient and your balance."
        receiver = data.fix_name(command_parts[1])
        try:
            amount = round(float(command_parts[2]), 1)
        except ValueError:
            return "Failed to send. Check recipient and your balance."
        if sender == receiver or amount <= 0:
            return "Failed to send. Check recipient and your balance."
        sender_balance = data.get_balance(sender)
        if sender_balance < amount:
            return "Failed to send. Check recipient and your balance."
        receiver_balance = data.get_balance(receiver)
        data.set_balance(sender, sender_balance - amount)
        data.set_balance(receiver, receiver_balance + amount)
        data.save_transaction(sender, receiver, amount)
        return f"Sent {amount:.1f} koins to {receiver}."

    elif command == "sub":
        if len(command_parts) != 4:
            return "Failed to make subscription. Ensure you have sufficient koins."
        payee = data.fix_name(command_parts[1])
        try:
            amount = round(float(command_parts[2]), 1)
        except ValueError:
            return "Failed to make subscription. Ensure you have sufficient koins."
        cycle_type = command_parts[3].lower()
        if sender == payee or amount <= 0 or cycle_type not in ["daily", "weekly", "monthly"]:
            return "Failed to make subscription. Ensure you have sufficient koins."
        sender_balance = data.get_balance(sender)
        if sender_balance < amount:
            return "Failed to make subscription. Ensure you have sufficient koins."
        receiver_balance = data.get_balance(payee)
        data.set_balance(sender, sender_balance - amount)
        data.set_balance(payee, receiver_balance + amount)
        data.save_transaction(sender, payee, amount)
        current_time = int(time.time())
        cycle_seconds = {"daily": 86400, "weekly": 604800, "monthly": 2592000}[cycle_type]
        next_payment_timestamp = current_time + cycle_seconds
        data.add_subscription(sender, payee, amount, cycle_type, current_time, next_payment_timestamp)
        return f"Successfully subscribed {cycle_type} to {payee} for {amount:.1f} koins."

    elif command == "can":
        if len(command_parts) != 2:
            return "No active subscription to " + command_parts[1] + "."
        payee_to_cancel = data.fix_name(command_parts[1])
        if data.remove_subscription(sender, payee_to_cancel):
            return f"Cancelled subscription to {payee_to_cancel}."
        else:
            return f"No active subscription to {payee_to_cancel}."

    elif command == "canall":
        removed_payees = data.remove_all_subscriptions_by_payer(sender)
        if removed_payees:
            return "Cancelled all subscriptions."
        else:
            return "No active subscriptions."

    elif command == "found":
        if len(command_parts) != 2:
            return "Failed to create company. Check your balance."
        try:
            initial_amount = round(float(command_parts[1]), 1)
        except ValueError:
            return "Failed to create company. Check your balance."
        company_name = sender + "company"
        sender_balance = data.get_balance(sender)
        if sender_balance < initial_amount or initial_amount <= 0:
            return "Failed to create company. Check your balance."
        if data.get_company_data(company_name) is not None:
            return "Failed to create company. Check your balance."
        data.set_balance(sender, sender_balance - initial_amount)
        data.set_balance(company_name, initial_amount)
        data.save_transaction(sender, company_name, initial_amount)
        if data.add_company(company_name, sender):
            return f"Company created with {initial_amount:.1f} koins."
        else:
            return "Failed to create company. Check your balance."

    elif command == "add":
        if len(command_parts) != 3:
            return "Failed to add user. Check company and permissions."
        company_name_arg = data.fix_name(command_parts[1])
        user_to_add = data.fix_name(command_parts[2])
        company_data = data.get_company_data(company_name_arg)
        if company_data is None:
            return "Failed to add user. Check company and permissions."
        if not data.is_company_member(company_name_arg, sender):
            return "Failed to add user. Check company and permissions."
        if user_to_add in company_data["members"]:
            return "Failed to add user. Check company and permissions."
        if data.add_company_member(company_name_arg, user_to_add):
            return f"Added {user_to_add} to company."
        else:
            return "Failed to add user. Check company and permissions."

    elif command == "sendco":
        if len(command_parts) != 4:
            return "Failed to send. Check company, permissions, and balance."
        company_name_arg = data.fix_name(command_parts[1])
        recipient = data.fix_name(command_parts[2])
        try:
            amount = round(float(command_parts[3]), 1)
        except ValueError:
            return "Failed to send. Check company, permissions, and balance."
        if amount <= 0 or sender == recipient:
            return "Failed to send. Check company, permissions, and balance."
        company_data = data.get_company_data(company_name_arg)
        if company_data is None or not data.is_company_member(company_name_arg, sender):
            return "Failed to send. Check company, permissions, and balance."
        company_balance = data.get_balance(company_name_arg)
        if company_balance < amount:
            return "Failed to send. Check company, permissions, and balance."
        recipient_balance = data.get_balance(recipient)
        data.set_balance(company_name_arg, company_balance - amount)
        data.set_balance(recipient, recipient_balance + amount)
        data.save_transaction(company_name_arg, recipient, amount)
        return f"Sent {amount:.1f} koins from {company_name_arg} to {recipient}."

    elif command == "print":
        if len(command_parts) != 2:
            return "Failed to mint. Check permissions and amount."
        if sender != data.get_current_holder("president"):
            return "Failed to mint. Check permissions and amount."
        try:
            amount = round(float(command_parts[1]), 1)
        except ValueError:
            return "Failed to mint. Check permissions and amount."
        if amount <= 0:
            return "Failed to mint. Check permissions and amount."
        bal = data.get_balance("officialtreasury")
        data.set_balance("officialtreasury", bal + amount)
        return f"Minted {amount:.1f} koins."

    elif command == "burn":
        if len(command_parts) != 2:
            return "Failed to burn. Check permissions and treasury balance."
        if sender != data.get_current_holder("president"):
            return "Failed to burn. Check permissions and treasury balance."
        try:
            amount = round(float(command_parts[1]), 1)
        except ValueError:
            return "Failed to burn. Check permissions and treasury balance."
        if amount <= 0:
            return "Failed to burn. Check permissions and treasury balance."
        bal = data.get_balance("officialtreasury")
        if bal < amount:
            return "Failed to burn. Check permissions and treasury balance."
        data.set_balance("officialtreasury", bal - amount)
        return f"Burned {amount:.1f} koins."

    elif command == "spend":
        if len(command_parts) != 3:
            return "Failed to send from treasury. Check permissions and balance."
        if sender != data.get_current_holder("president"):
            return "Failed to send from treasury. Check permissions and balance."
        try:
            amount = round(float(command_parts[1]), 1)
        except ValueError:
            return "Failed to send from treasury. Check permissions and balance."
        if amount <= 0:
            return "Failed to send from treasury. Check permissions and balance."
        target = data.fix_name(command_parts[2])
        treasury_bal = data.get_balance("officialtreasury")
        if treasury_bal < amount:
            return "Failed to send from treasury. Check permissions and balance."
        recipient_bal = data.get_balance(target)
        data.set_balance("officialtreasury", treasury_bal - amount)
        data.set_balance(target, recipient_bal + amount)
        data.save_transaction("officialtreasury", target, amount)
        return f"Treasury sent {amount:.1f} koins to {target}."

    else:
        return "Unknown command."

def comment_listener_thread(project):
    while True:
        try:
            comments = project.comments(limit=30)
            for comment in reversed(comments):
                if not data.is_comment_processed(comment.id):
                    content = comment.content
                    author = comment.author_name
                    command_parts = content.strip().split(" ")
                    if not command_parts or not command_parts[0]:
                        data.add_processed_comment(comment.id)
                        continue
                    first_word = command_parts[0].lower()
                    clean_word = first_word.lstrip("!")
                    known_direct_commands = ["s", "sub", "can", "canall", "found", "add", "sendco", "print", "burn", "spend"]
                    if clean_word == "n":
                        natural = " ".join(command_parts[1:])
                        process_natural_language_command(author, natural)
                    elif clean_word in known_direct_commands:
                        process_comment_command(author, command_parts)
                    data.add_processed_comment(comment.id)
        except Exception as e:
            print("Error in comment_listener_thread:", e)
        time.sleep(5)

def subscription_processor_thread():
    while True:
        try:
            now = int(time.time())
            all_subs = data.get_all_subscriptions()
            for sub in all_subs:
                if now >= sub["next_payment_timestamp"]:
                    payer = sub["payer"]
                    payee = sub["payee"]
                    amount = sub["amount"]
                    cycle = sub["cycle"]
                    payer_bal = data.get_balance(payer)
                    if payer_bal >= amount:
                        payee_bal = data.get_balance(payee)
                        data.set_balance(payer, payer_bal - amount)
                        data.set_balance(payee, payee_bal + amount)
                        data.save_transaction(payer, payee, amount)
                        last_paid = now
                        cycle_seconds = CYCLE_TIMES[cycle].total_seconds()
                        next_payment = now + cycle_seconds
                        sub["last_paid_timestamp"] = last_paid
                        sub["next_payment_timestamp"] = next_payment
            data._subscriptions_save(all_subs)
        except Exception as e:
            print("Error in subscription_processor_thread:", e)
        time.sleep(60)

def election_thread():
    while True:
        try:
            data.check_and_update_elections()
        except Exception as e:
            print("Error in election_thread:", e)
        time.sleep(60)

def process_natural_language_command(requester, natural_command_text):
    # Placeholder: You may want to implement Gemini or another LLM integration.
    # For now, just return not supported.
    return "Natural language commands not supported."
