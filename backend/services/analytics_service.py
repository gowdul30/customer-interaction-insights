"""Analytics service — aggregation logic over call data."""
from collections import Counter, defaultdict
from datetime import datetime


class AnalyticsService:
    def __init__(self, calls):
        self.calls = calls

    def _filter(self, client=None, start_date=None, end_date=None):
        filtered = self.calls
        if client and client != "All":
            filtered = [c for c in filtered if c["client"] == client]
        if start_date:
            filtered = [c for c in filtered if c["call_metadata"]["date"] >= start_date]
        if end_date:
            filtered = [c for c in filtered if c["call_metadata"]["date"] <= end_date]
        return filtered

    def get_overview(self, client=None, start_date=None, end_date=None):
        calls = self._filter(client, start_date, end_date)
        if not calls:
            return {"total_calls":0,"escalation_rate":0,"avg_csat":0,"resolution_rate":0,"avg_duration":0,"callback_count":0}

        total = len(calls)
        escalated = sum(1 for c in calls if c["nlp_analysis"]["escalation"]["escalated"])
        resolved = sum(1 for c in calls if c["call_metadata"]["issue_resolved"])
        callbacks = sum(1 for c in calls if c["nlp_analysis"]["callback_intent"]["callback_requested"])
        csat_scores = [c["feedback"]["csat_score"] for c in calls if c["feedback"]["post_call_survey_completed"] and c["feedback"]["csat_score"] > 0]
        avg_csat = round(sum(csat_scores) / len(csat_scores), 2) if csat_scores else 0
        avg_duration = round(sum(c["call_metadata"]["duration_seconds"] for c in calls) / total)
        sentiments = [c["nlp_analysis"]["customer_tone"]["sentiment_score"] for c in calls]
        avg_sentiment = round(sum(sentiments) / len(sentiments), 2) if sentiments else 0

        # Monthly trends for sparklines
        monthly = defaultdict(lambda: {"calls":0,"escalated":0,"resolved":0,"csat_sum":0,"csat_count":0})
        for c in calls:
            month = c["call_metadata"]["date"][:7]
            monthly[month]["calls"] += 1
            if c["nlp_analysis"]["escalation"]["escalated"]:
                monthly[month]["escalated"] += 1
            if c["call_metadata"]["issue_resolved"]:
                monthly[month]["resolved"] += 1
            if c["feedback"]["post_call_survey_completed"] and c["feedback"]["csat_score"] > 0:
                monthly[month]["csat_sum"] += c["feedback"]["csat_score"]
                monthly[month]["csat_count"] += 1

        trends = []
        for month in sorted(monthly.keys()):
            m = monthly[month]
            trends.append({
                "month": month,
                "calls": m["calls"],
                "escalation_rate": round(m["escalated"]/m["calls"], 3) if m["calls"] else 0,
                "resolution_rate": round(m["resolved"]/m["calls"], 3) if m["calls"] else 0,
                "avg_csat": round(m["csat_sum"]/m["csat_count"], 2) if m["csat_count"] else 0,
            })

        return {
            "total_calls": total,
            "escalation_rate": round(escalated/total, 3),
            "resolution_rate": round(resolved/total, 3),
            "avg_csat": avg_csat,
            "avg_duration": avg_duration,
            "avg_sentiment": avg_sentiment,
            "callback_count": callbacks,
            "escalated_count": escalated,
            "resolved_count": resolved,
            "trends": trends,
        }

    def get_root_causes(self, client=None, start_date=None, end_date=None):
        calls = self._filter(client, start_date, end_date)
        # Distribution by category
        cat_counts = Counter(c["nlp_analysis"]["root_cause"]["category"] for c in calls)
        total = len(calls)
        distribution = [{"category": k, "count": v, "percentage": round(v/total, 3)} for k, v in cat_counts.most_common()]

        # Monthly trend per category
        monthly = defaultdict(lambda: defaultdict(int))
        for c in calls:
            month = c["call_metadata"]["date"][:7]
            monthly[month][c["nlp_analysis"]["root_cause"]["category"]] += 1
        all_cats = sorted(cat_counts.keys())
        trends = [{"month": m, **{cat: monthly[m].get(cat, 0) for cat in all_cats}} for m in sorted(monthly.keys())]

        # Top recurring specific causes
        cause_counter = Counter(c["nlp_analysis"]["root_cause"]["detected_cause"] for c in calls)
        top_recurring = [{"cause": cause, "count": count, "recurrence_score": round(min(count/10, 1.0), 2)} for cause, count in cause_counter.most_common(10)]

        # Root cause by client
        by_client = defaultdict(lambda: Counter())
        for c in calls:
            by_client[c["client"]][c["nlp_analysis"]["root_cause"]["category"]] += 1
        client_breakdown = {cl: dict(counts) for cl, counts in by_client.items()}

        return {"distribution": distribution, "trends": trends, "top_recurring": top_recurring, "by_client": client_breakdown}

    def get_escalations(self, client=None, start_date=None, end_date=None):
        calls = self._filter(client, start_date, end_date)
        escalated_calls = [c for c in calls if c["nlp_analysis"]["escalation"]["escalated"]]
        total = len(calls)
        esc_total = len(escalated_calls)

        # By client
        by_client = defaultdict(lambda: {"total":0,"escalated":0})
        for c in calls:
            by_client[c["client"]]["total"] += 1
            if c["nlp_analysis"]["escalation"]["escalated"]:
                by_client[c["client"]]["escalated"] += 1
        client_rates = [{"client": cl, "total": d["total"], "escalated": d["escalated"],
                         "rate": round(d["escalated"]/d["total"], 3)} for cl, d in sorted(by_client.items())]

        # Trigger signals
        signal_counter = Counter()
        for c in escalated_calls:
            for s in c["nlp_analysis"]["escalation"]["escalation_signals"]:
                signal_counter[s] += 1
        top_signals = [{"signal": s, "count": cnt} for s, cnt in signal_counter.most_common(10)]

        # By root cause
        by_rc = defaultdict(lambda: {"total":0,"escalated":0})
        for c in calls:
            rc = c["nlp_analysis"]["root_cause"]["category"]
            by_rc[rc]["total"] += 1
            if c["nlp_analysis"]["escalation"]["escalated"]:
                by_rc[rc]["escalated"] += 1
        rc_rates = [{"category": rc, "total": d["total"], "escalated": d["escalated"],
                     "rate": round(d["escalated"]/d["total"], 3)} for rc, d in sorted(by_rc.items())]

        # Monthly escalation trend
        monthly = defaultdict(lambda: {"total":0,"escalated":0})
        for c in calls:
            month = c["call_metadata"]["date"][:7]
            monthly[month]["total"] += 1
            if c["nlp_analysis"]["escalation"]["escalated"]:
                monthly[month]["escalated"] += 1
        trends = [{"month": m, "total": d["total"], "escalated": d["escalated"],
                   "rate": round(d["escalated"]/d["total"], 3)} for m, d in sorted(monthly.items())]

        return {"total_escalated": esc_total, "escalation_rate": round(esc_total/total, 3) if total else 0,
                "by_client": client_rates, "top_signals": top_signals, "by_root_cause": rc_rates, "trends": trends}

    def get_sentiment(self, client=None, start_date=None, end_date=None):
        calls = self._filter(client, start_date, end_date)

        # Overall distribution
        tone_counts = Counter(c["nlp_analysis"]["customer_tone"]["overall"] for c in calls)
        distribution = [{"tone": t, "count": c, "percentage": round(c/len(calls), 3)} for t, c in tone_counts.most_common()]

        # Sentiment score distribution (buckets)
        buckets = {"very_negative":0,"negative":0,"neutral":0,"positive":0,"very_positive":0}
        for c in calls:
            s = c["nlp_analysis"]["customer_tone"]["sentiment_score"]
            if s < -0.6: buckets["very_negative"] += 1
            elif s < -0.2: buckets["negative"] += 1
            elif s < 0.2: buckets["neutral"] += 1
            elif s < 0.6: buckets["positive"] += 1
            else: buckets["very_positive"] += 1
        score_distribution = [{"bucket": k, "count": v} for k, v in buckets.items()]

        # Monthly sentiment trend
        monthly = defaultdict(list)
        for c in calls:
            month = c["call_metadata"]["date"][:7]
            monthly[month].append(c["nlp_analysis"]["customer_tone"]["sentiment_score"])
        trends = [{"month": m, "avg_sentiment": round(sum(scores)/len(scores), 3), "count": len(scores)} for m, scores in sorted(monthly.items())]

        # Sentiment vs CSAT correlation
        csat_sentiment = []
        for c in calls:
            if c["feedback"]["post_call_survey_completed"] and c["feedback"]["csat_score"] > 0:
                csat_sentiment.append({"sentiment_score": c["nlp_analysis"]["customer_tone"]["sentiment_score"],
                                       "csat_score": c["feedback"]["csat_score"], "client": c["client"]})

        # Sentiment by client
        by_client = defaultdict(list)
        for c in calls:
            by_client[c["client"]].append(c["nlp_analysis"]["customer_tone"]["sentiment_score"])
        client_sentiment = [{"client": cl, "avg_sentiment": round(sum(s)/len(s), 3), "count": len(s)} for cl, s in sorted(by_client.items())]

        return {"distribution": distribution, "score_distribution": score_distribution, "trends": trends,
                "csat_correlation": csat_sentiment[:100], "by_client": client_sentiment}

    def get_agents(self, client=None, start_date=None, end_date=None):
        calls = self._filter(client, start_date, end_date)

        agent_stats = defaultdict(lambda: {"name":"","calls":0,"resolved":0,"escalated":0,"csat_sum":0,"csat_count":0,"sentiment_sum":0,"total_duration":0})
        for c in calls:
            aid = c["call_metadata"]["agent_id"]
            a = agent_stats[aid]
            a["name"] = c["call_metadata"]["agent_name"]
            a["calls"] += 1
            a["total_duration"] += c["call_metadata"]["duration_seconds"]
            a["sentiment_sum"] += c["nlp_analysis"]["customer_tone"]["sentiment_score"]
            if c["call_metadata"]["issue_resolved"]:
                a["resolved"] += 1
            if c["nlp_analysis"]["escalation"]["escalated"]:
                a["escalated"] += 1
            if c["feedback"]["post_call_survey_completed"] and c["feedback"]["csat_score"] > 0:
                a["csat_sum"] += c["feedback"]["csat_score"]
                a["csat_count"] += 1

        leaderboard = []
        for aid, a in agent_stats.items():
            if a["calls"] < 3:
                continue
            leaderboard.append({
                "agent_id": aid,
                "agent_name": a["name"],
                "total_calls": a["calls"],
                "resolution_rate": round(a["resolved"]/a["calls"], 3),
                "escalation_rate": round(a["escalated"]/a["calls"], 3),
                "avg_csat": round(a["csat_sum"]/a["csat_count"], 2) if a["csat_count"] else 0,
                "avg_sentiment": round(a["sentiment_sum"]/a["calls"], 3),
                "avg_duration": round(a["total_duration"]/a["calls"]),
                "quality_score": round(
                    (a["resolved"]/a["calls"])*0.4 +
                    (1 - a["escalated"]/a["calls"])*0.3 +
                    (a["csat_sum"]/a["csat_count"]/5 if a["csat_count"] else 0.5)*0.3, 3),
            })
        leaderboard.sort(key=lambda x: x["quality_score"], reverse=True)
        return {"leaderboard": leaderboard, "total_agents": len(leaderboard)}

    def get_clients(self):
        return sorted(set(c["client"] for c in self.calls))
