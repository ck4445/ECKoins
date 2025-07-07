import scratchattach as sa
import threading
import data
import commands

with open('secrets/session_id.txt', 'r') as session_id_txt:
    session_id = session_id_txt.read().strip()

project_id = 1169901452
session = sa.login_by_id(session_id, username='OfficialECKO')
cloud = session.connect_cloud(project_id)
client = cloud.requests(used_cloud_vars=['1\u200e', '2\u200e', '3\u200e', '4\u200e'])
project = session.connect_project(project_id)


@client.request
def balance():
    requester = data.fix_name(client.get_requester())
    bal = data.get_balance(requester)
    notifs = data.get_notifications(requester)
    if not notifs:
        data.add_notification(requester, 'Welcome! No new notifications.')
    return f"{bal:.1f}"


@client.request
def get_preferences():
    requester = data.fix_name(client.get_requester())
    prefs = data.get_preferences(requester)
    return [prefs[i] for i in prefs]


@client.request
def set_preferences(theme, mute):
    requester = data.fix_name(client.get_requester())
    data.set_preferences(requester, theme, mute)
    return 'updated preferences'


@client.request
def give(amount, user):
    try:
        amount = round(float(amount), 1)
    except ValueError:
        return 'Invalid amount.'
    sender = data.fix_name(client.get_requester())
    user = data.fix_name(user)
    if sender == user:
        return 'You cannot send bits to yourself.'
    if amount <= 0:
        return 'Amount must be positive.'
    sender_balance = data.get_balance(sender)
    if sender_balance < amount:
        return 'Insufficient balance.'
    receiver_balance = data.get_balance(user)
    data.set_balance(sender, sender_balance - amount)
    data.set_balance(user, receiver_balance + amount)
    ts = data.generate_readable_timestamp()
    data.add_notification(user, f"{ts} - {sender} gave you {amount:.1f} bits!")
    data.add_notification(sender, f"{ts} - You gave {amount:.1f} bits to {user}!")
    data.save_transaction(sender, user, amount)
    return f"{data.get_balance(sender):.1f}"


@client.request
def search(user):
    user = data.fix_name(user)
    bal = data.get_balance(user)
    if bal is not None:
        return f"{user} has {bal:.1f} bits!"
    return f"{user}'s balance couldn't be found. Did you spell it right?"


@client.request
def leaderboard():
    return data.create_leaderboard()


@client.request
def notifications():
    requester = data.fix_name(client.get_requester())
    notifs = data.get_notifications(requester)
    if not notifs:
        return 'No notifications!'
    return notifs


@client.request
def vote(candidate):
    voter = data.fix_name(client.get_requester())
    candidate = data.fix_name(candidate)
    if data.vote_candidate(candidate, voter):
        return 'vote recorded'
    return 'already voted'


@client.request
def get_candidates():
    return data.get_candidates()


@client.request
def getpolitics():
    return data.get_politics()


@client.request
def getemployees(company):
    """
    Returns the list of employees (members) for a given company.
    """
    company_fixed = data.fix_name(company)
    company_data = data.get_company_data(company_fixed)
    if not company_data:
        return []
    return company_data.get("members", [])


@client.request
def command(p1=None, p2=None, p3=None, p4=None):
    """
    Accept up to four command arguments as parameters.
    These are joined with spaces and processed as a command string, for compatibility with all existing commands.
    Example: command('sub', 'targetuser', '10', 'weekly')
    """
    requester = data.fix_name(client.get_requester())
    params = [str(x).strip() for x in (p1, p2, p3, p4) if x is not None and str(x).strip() != ""]
    if not params:
        return 'No command provided'
    if not params[0].startswith('!'):
        params[0] = '!' + params[0]
    if params[0].lower().lstrip('!') == "n":
        if len(params) > 1:
            natural = " ".join(params[1:])
            commands.process_natural_language_command(requester, natural)
    else:
        commands.process_comment_command(requester, params)
    return 'ok'


@client.event
def on_ready():
    print('Request handler is running')


def main():
    data.verify_balance_integrity()
    data.backup_every_n_minutes(10, 10)
    comment_thread = threading.Thread(target=commands.comment_listener_thread, args=(project,), daemon=True)
    comment_thread.start()
    subscription_thread = threading.Thread(target=commands.subscription_processor_thread, daemon=True)
    subscription_thread.start()
    election_thread = threading.Thread(target=commands.election_thread, daemon=True)
    election_thread.start()
    client.start(thread=True)


if __name__ == '__main__':
    main()
