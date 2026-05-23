#!/usr/bin/env python3
"""Generate 550 realistic call analysis records for Customer Interaction Insights."""

import json, random, os
from datetime import datetime, timedelta

random.seed(42)

NUM_CALLS = 550
DATE_START = datetime(2024, 1, 1)
DATE_END = datetime(2024, 12, 31)

CLIENTS = {
    "Verizon": {"weight": 0.28, "prefix": "VRZ"},
    "Wells Fargo": {"weight": 0.24, "prefix": "WF"},
    "AT&T": {"weight": 0.20, "prefix": "ATT"},
    "Comcast": {"weight": 0.16, "prefix": "CMC"},
    "T-Mobile": {"weight": 0.12, "prefix": "TMO"},
}

AGENTS = [
    ("AGT-1001","Sarah Mitchell"),("AGT-1002","James Rodriguez"),("AGT-1003","Emily Chen"),
    ("AGT-1004","Michael Thompson"),("AGT-1005","Jessica Patel"),("AGT-1006","David Kim"),
    ("AGT-1007","Amanda Foster"),("AGT-1008","Robert Williams"),("AGT-1009","Lisa Nguyen"),
    ("AGT-1010","Chris Martinez"),("AGT-1011","Sophia Brown"),("AGT-1012","Daniel Lee"),
    ("AGT-1013","Rachel Green"),("AGT-1014","Kevin Anderson"),("AGT-1015","Maria Garcia"),
    ("AGT-1016","Alex Johnson"),("AGT-1017","Nicole Davis"),("AGT-1018","Brian Wilson"),
    ("AGT-1019","Stephanie Taylor"),("AGT-1020","Mark Thomas"),("AGT-1021","Ashley Jackson"),
    ("AGT-1022","Ryan White"),("AGT-1023","Jennifer Harris"),("AGT-1024","Tyler Clark"),
    ("AGT-1025","Megan Lewis"),
]

# Agent quality profiles
AGENT_QUALITY = {a[0]: {"resolve_rate": random.uniform(0.55, 0.92), "empathy": random.uniform(0.5, 0.95)} for a in AGENTS}

QUEUES = ["billing_support","technical_support","general_inquiry","retention","account_services"]

ROOT_CAUSES = {
    "billing_error": [
        "Auto-renewal charge applied without prior notification",
        "Duplicate charge for same billing period",
        "Incorrect proration after plan change",
        "Late payment fee despite on-time payment",
        "Promotional discount not applied as promised",
        "Cancelled service still being billed",
    ],
    "network_issue": [
        "Persistent dropped calls in customer area",
        "Slow data speeds despite unlimited plan",
        "No coverage in newly relocated area",
        "5G unavailable in advertised coverage zone",
    ],
    "service_outage": [
        "Regional outage affecting multiple customers",
        "Planned maintenance not communicated",
        "Intermittent disruption lasting over 24 hours",
        "Online portal down during billing cycle",
    ],
    "policy_confusion": [
        "Customer misunderstood early termination terms",
        "Unclear data throttling policy",
        "Confusion about international calling rates",
        "Misunderstanding of upgrade eligibility",
    ],
    "account_access": [
        "Locked out after failed password attempts",
        "Two-factor authentication code not received",
        "Account merged incorrectly during migration",
        "Unauthorized changes detected on account",
    ],
    "agent_error": [
        "Previous agent gave incorrect pricing info",
        "Agent failed to process prior cancellation request",
        "Wrong plan applied during setup",
        "Agent did not document callback commitment",
    ],
    "system_bug": [
        "Payment system showing incorrect balance",
        "Auto-pay setup failing without error",
        "App displaying wrong data usage metrics",
    ],
}

CLIENT_ROOT_WEIGHTS = {
    "Verizon":     {"billing_error":0.35,"network_issue":0.25,"service_outage":0.10,"policy_confusion":0.10,"account_access":0.08,"agent_error":0.07,"system_bug":0.05},
    "Wells Fargo": {"billing_error":0.20,"network_issue":0.05,"service_outage":0.05,"policy_confusion":0.30,"account_access":0.20,"agent_error":0.10,"system_bug":0.10},
    "AT&T":        {"billing_error":0.30,"network_issue":0.25,"service_outage":0.15,"policy_confusion":0.10,"account_access":0.08,"agent_error":0.07,"system_bug":0.05},
    "Comcast":     {"billing_error":0.20,"network_issue":0.15,"service_outage":0.30,"policy_confusion":0.10,"account_access":0.08,"agent_error":0.12,"system_bug":0.05},
    "T-Mobile":    {"billing_error":0.30,"network_issue":0.20,"service_outage":0.10,"policy_confusion":0.15,"account_access":0.10,"agent_error":0.08,"system_bug":0.07},
}

INTENT_MAP = {
    "billing_error": ("billing_dispute", ["refund_request","payment_inquiry"]),
    "network_issue": ("service_complaint", ["technical_support","cancellation"]),
    "service_outage": ("service_complaint", ["technical_support","general_inquiry"]),
    "policy_confusion": ("account_inquiry", ["general_inquiry","plan_change"]),
    "account_access": ("account_inquiry", ["technical_support","general_inquiry"]),
    "agent_error": ("service_complaint", ["escalation_request","refund_request"]),
    "system_bug": ("technical_support", ["account_inquiry","general_inquiry"]),
}

ESCALATION_SIGNALS = [
    "requested supervisor","threatened to cancel service","raised voice detected",
    "used profanity","mentioned competitor","mentioned legal action",
    "repeated complaint multiple times","demanded immediate resolution",
    "expressed extreme dissatisfaction","asked for corporate contact",
]

TONE_PROGRESSIONS = {
    "angry":      [["neutral","frustrated","angry"],["frustrated","angry","very_angry"],["neutral","angry"]],
    "frustrated": [["neutral","frustrated"],["neutral","concerned","frustrated"],["frustrated","neutral","frustrated"]],
    "neutral":    [["neutral"],["neutral","satisfied"],["neutral","concerned","neutral"]],
    "satisfied":  [["neutral","satisfied"],["concerned","neutral","satisfied"],["neutral","relieved","satisfied"]],
}

COMMENTS_BY_SENTIMENT = {
    "negative": [
        "Wasted {mins} minutes and still no resolution. Very disappointed.",
        "This is the {nth} time I've called about the same issue. Unacceptable.",
        "Agent was unhelpful and seemed disinterested in my problem.",
        "I'm seriously considering switching to a competitor.",
        "Terrible experience. No one seems to know what they're doing.",
        "Still waiting for a callback that was promised {days} days ago.",
    ],
    "neutral": [
        "Issue was partially addressed but I need to follow up.",
        "Agent was polite but couldn't fully resolve my concern.",
        "Average experience. Nothing special but not terrible.",
        "Took longer than expected but got some answers.",
    ],
    "positive": [
        "Agent was very helpful and resolved my issue quickly!",
        "Great experience, {agent} went above and beyond.",
        "Issue fixed on the first call. Very impressed.",
        "Professional and efficient service. Thank you!",
        "Best customer service experience I've had in a while.",
    ],
}

def pick_weighted(weights_dict):
    items = list(weights_dict.keys())
    weights = list(weights_dict.values())
    return random.choices(items, weights=weights, k=1)[0]

def random_date():
    delta = (DATE_END - DATE_START).days
    d = DATE_START + timedelta(days=random.randint(0, delta))
    # More calls on weekdays
    while d.weekday() >= 5 and random.random() < 0.6:
        d = DATE_START + timedelta(days=random.randint(0, delta))
    return d

def generate_call(idx, override_datetime=None):
    # Pick client
    client = pick_weighted({k: v["weight"] for k, v in CLIENTS.items()})
    prefix = CLIENTS[client]["prefix"]
    call_id = f"{prefix}-2024-{idx:05d}"

    # Date & time
    if override_datetime:
        date = override_datetime
        hour = date.hour
        minute = date.minute
        second = date.second
    else:
        date = random_date()
        hour = random.choices(range(8, 22), weights=[2,4,6,8,10,10,8,8,6,5,4,3,2,1], k=1)[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

    # Root cause
    rc_category = pick_weighted(CLIENT_ROOT_WEIGHTS[client])
    rc_cause = random.choice(ROOT_CAUSES[rc_category])
    rc_confidence = round(random.uniform(0.82, 0.98), 2)

    # Intent
    primary_intent, secondary_options = INTENT_MAP[rc_category]
    secondary_intent = random.choice(secondary_options)
    intent_confidence = round(random.uniform(0.85, 0.98), 2)

    # Agent
    agent_id, agent_name = random.choice(AGENTS)
    aq = AGENT_QUALITY[agent_id]

    # Resolution depends on agent quality and root cause severity
    severity = {"billing_error":0.6,"network_issue":0.5,"service_outage":0.3,"policy_confusion":0.7,"account_access":0.6,"agent_error":0.5,"system_bug":0.4}
    resolve_chance = aq["resolve_rate"] * severity.get(rc_category, 0.5)
    issue_resolved = random.random() < resolve_chance

    # Duration (unresolved calls tend to be longer)
    base_duration = random.randint(180, 600)
    if not issue_resolved:
        base_duration += random.randint(100, 400)
    duration = min(base_duration, 1500)

    # Sentiment
    if issue_resolved:
        sentiment_score = round(random.uniform(-0.2, 0.8), 2)
        overall_tone = random.choices(["satisfied","neutral","frustrated"], weights=[0.5,0.35,0.15], k=1)[0]
    else:
        sentiment_score = round(random.uniform(-0.95, 0.1), 2)
        overall_tone = random.choices(["angry","frustrated","neutral"], weights=[0.4,0.45,0.15], k=1)[0]

    tone_prog = random.choice(TONE_PROGRESSIONS.get(overall_tone, [["neutral"]]))

    # Escalation
    escalation_base = 0.15 if issue_resolved else 0.55
    if overall_tone == "angry":
        escalation_base += 0.2
    escalated = random.random() < min(escalation_base, 0.85)

    esc_trigger = ""
    esc_signals = []
    esc_confidence = 0.0
    if escalated:
        esc_trigger = f"Customer requested supervisor after agent could not resolve {rc_category.replace('_',' ')} issue"
        esc_signals = random.sample(ESCALATION_SIGNALS, k=random.randint(2, 4))
        esc_confidence = round(random.uniform(0.88, 0.99), 2)

    # Callback
    callback_requested = (not issue_resolved) and random.random() < 0.7
    callback_reason = ""
    callback_type = ""
    cb_confidence = 0.0
    if callback_requested:
        callback_reason = f"Issue unresolved — {'supervisor' if escalated else 'agent'} callback promised within {random.choice([24,48])} hours"
        callback_type = random.choice(["agent_promised","supervisor_required","customer_requested"])
        cb_confidence = round(random.uniform(0.88, 0.97), 2)

    # CSAT
    survey_completed = random.random() < 0.65
    csat = 0
    comment = ""
    if survey_completed:
        if issue_resolved and overall_tone in ("satisfied","neutral"):
            csat = random.choices([4,5,3], weights=[0.4,0.4,0.2], k=1)[0]
            comment = random.choice(COMMENTS_BY_SENTIMENT["positive"]).format(agent=agent_name, mins=duration//60)
        elif overall_tone == "angry" or (not issue_resolved and overall_tone == "frustrated"):
            csat = random.choices([1,2], weights=[0.4,0.6], k=1)[0]
            comment = random.choice(COMMENTS_BY_SENTIMENT["negative"]).format(mins=duration//60, nth=random.choice(["2nd","3rd","4th"]), days=random.randint(2,7))
        else:
            csat = random.choices([2,3,4], weights=[0.3,0.5,0.2], k=1)[0]
            comment = random.choice(COMMENTS_BY_SENTIMENT["neutral"])

    # Queue
    queue_map = {"billing_error":"billing_support","network_issue":"technical_support","service_outage":"technical_support",
                 "policy_confusion":"general_inquiry","account_access":"account_services","agent_error":"billing_support","system_bug":"technical_support"}
    queue = queue_map.get(rc_category, "general_inquiry")

    # Transcript summary
    issue_desc = rc_cause.lower()
    resolution_desc = f"Agent resolved the issue by {random.choice(['applying a credit','correcting the charge','updating the account','providing a workaround','processing the request'])}" if issue_resolved else f"Agent was unable to resolve without {random.choice(['supervisor approval','system access','further investigation','manager override'])}"
    outcome = "Customer expressed satisfaction with the resolution." if issue_resolved else f"Customer {'demanded escalation' if escalated else 'was informed a callback would be scheduled'}."
    summary = f"Customer called regarding {issue_desc}. {resolution_desc}. {outcome}"

    call_summary = f"Customer {'reported' if not issue_resolved else 'inquired about'} {issue_desc}. " \
                   f"{'Issue was resolved during the call.' if issue_resolved else 'Issue remains unresolved at call end.'} " \
                   f"{'Escalated to supervisor queue.' if escalated else ''} " \
                   f"{'Callback scheduled.' if callback_requested else ''} " \
                   f"CSAT: {csat}/5." if survey_completed else f"Customer reported {issue_desc}. {'Resolved.' if issue_resolved else 'Unresolved.'}"

    return {
        "call_id": call_id,
        "client": client,
        "call_metadata": {
            "date": date.strftime("%Y-%m-%d"),
            "time": f"{hour:02d}:{minute:02d}:{second:02d}",
            "duration_seconds": duration,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "channel": random.choices(["inbound","inbound","outbound","transfer"], weights=[0.6,0.2,0.1,0.1], k=1)[0],
            "queue": queue,
            "issue_resolved": issue_resolved,
        },
        "transcript_summary": summary,
        "nlp_analysis": {
            "customer_intent": {
                "primary_intent": primary_intent,
                "secondary_intent": secondary_intent,
                "confidence": intent_confidence,
            },
            "root_cause": {
                "detected_cause": rc_cause,
                "category": rc_category,
                "confidence": rc_confidence,
            },
            "escalation": {
                "escalated": escalated,
                "escalation_trigger": esc_trigger,
                "escalation_signals": esc_signals,
                "confidence": esc_confidence,
            },
            "callback_intent": {
                "callback_requested": callback_requested,
                "reason": callback_reason,
                "callback_type": callback_type,
                "confidence": cb_confidence,
            },
            "customer_tone": {
                "overall": overall_tone,
                "tone_progression": tone_prog,
                "sentiment_score": sentiment_score,
            },
            "call_summary": call_summary,
        },
        "feedback": {
            "post_call_survey_completed": survey_completed,
            "csat_score": csat,
            "customer_comment": comment,
        },
    }

def main():
    calls = [generate_call(i + 1) for i in range(NUM_CALLS)]
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "calls.json")
    with open(out_path, "w") as f:
        json.dump(calls, f, indent=2)
    print(f"Generated {len(calls)} call records -> {out_path}")

    # Print summary stats
    clients = {}
    for c in calls:
        cl = c["client"]
        clients.setdefault(cl, {"total":0,"escalated":0,"resolved":0})
        clients[cl]["total"] += 1
        if c["nlp_analysis"]["escalation"]["escalated"]:
            clients[cl]["escalated"] += 1
        if c["call_metadata"]["issue_resolved"]:
            clients[cl]["resolved"] += 1
    print("\nSummary:")
    for cl, s in sorted(clients.items()):
        print(f"  {cl}: {s['total']} calls, {s['escalated']} escalated ({s['escalated']/s['total']*100:.0f}%), {s['resolved']} resolved ({s['resolved']/s['total']*100:.0f}%)")

if __name__ == "__main__":
    main()
