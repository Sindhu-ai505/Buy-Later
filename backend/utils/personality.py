"""backend/utils/personality.py

Personality System:
User chooses: Best Friend, Spouse, Parent, Child, Sibling, Professional Advisor.
Personality alters ONLY phrasing and emotional tone (explanation text, challenge text).
It NEVER modifies scores, impulse probabilities, or recommendation decisions.
"""

from typing import Dict, Any, List

PERSONALITY_PROFILES = {
    "Best Friend": {
        "greeting": "Yo {name}! Let's keep it 100% real about your spending. 😂",
        "buy_now": "Honestly bro, go for it! You genuinely need this and it makes complete sense. Enjoy it! 🎉",
        "consider": "Bro, pause for a second. It's not a bad deal, but do you really need it right now? Think about it.",
        "wait_7days": "Bro, be honest 😂! Don't let late-night cravings or flash sales fool you. Let's wait 7 days. If you still want it then, we talk.",
        "dont_buy": "Hard pass, my friend! 🚫 You already know deep down this is pure impulse hype. Save your cash for things that actually matter!",
        "challenge_intro": "Look, playing devil's advocate here: why this might actually not be the worst purchase in the world:",
    },
    "Spouse": {
        "greeting": "Hey darling {name}, let's take a sensible look at our budget together.",
        "buy_now": "This looks like a great and well-thought-out purchase for you. Go ahead, we have planned for this! ❤️",
        "consider": "Honey, let's talk about this before tapping buy. Does this align with our priorities this month?",
        "wait_7days": "Let's put this in the 7-day cooling-off jar, sweetheart. If we still feel it brings genuine value next week, we'll get it.",
        "dont_buy": "We really shouldn't buy this right now. Our household budget and upcoming goals are more important than another quick buy.",
        "challenge_intro": "Fair is fair—here are the genuine points in favor of getting this:",
    },
    "Parent": {
        "greeting": "Dear {name}, remember that money earned with hard work shouldn't be spent without careful thought.",
        "buy_now": "You have earned this and it fulfills a real, practical need. You have our blessing to buy it.",
        "consider": "Think carefully about whether you will still use this in six months, or if it will just gather dust.",
        "wait_7days": "Sleep on it for 7 days. If it's a real necessity, waiting one week won't hurt at all.",
        "dont_buy": "You do not need this right now. Do not get swayed by flashy internet discounts. Save your hard-earned money.",
        "challenge_intro": "Looking at the practical utility, here is what speaks in favor of this item:",
    },
    "Child": {
        "greeting": "Hey {name}! Are we buying something super exciting today?! 🎈",
        "buy_now": "Yay! This looks super useful and you totally deserve this awesome treat! 🚀",
        "consider": "Hmm, it looks cool, but are you sure you won't get bored of it after two days?",
        "wait_7days": "Can we make a secret countdown for 7 days? If you still want it when the timer rings, we can buy it!",
        "dont_buy": "You already have cool stuff at home! Let's save the coins for an epic adventure instead! 🍦",
        "challenge_intro": "Wait, but hear me out! Here is why this item is actually pretty awesome:",
    },
    "Sibling": {
        "greeting": "Hey {name}, don't pretend you're not trying to buy something unnecessary again! 😏",
        "buy_now": "Alright, credit where it's due: this actually looks legitimate. Get it before you change your mind.",
        "consider": "Are you really going to use this, or is this going into the pile of stuff you never touch?",
        "wait_7days": "Give it a week, seriously. If you're still obsessing over it in 7 days, then fine, but don't rush it.",
        "dont_buy": "Classic impulse move! 💀 You definitely don't need this. Save your money, thank me later.",
        "challenge_intro": "Okay fine, defending you for once: here's why you could argue this makes sense:",
    },
    "Professional Advisor": {
        "greeting": "Good day {name}. Let us conduct a structured fiscal evaluation of this proposed expenditure.",
        "buy_now": "Expenditure validated. The item exhibits high functional necessity and aligns with your current liquidity allocations.",
        "consider": "Discretionary purchase alert. The utility payoff is borderline relative to your prevailing savings trajectory.",
        "wait_7days": "A mandatory 7-day cooling-off protocol is recommended to mitigate cognitive biases and temporary promotional pressure.",
        "dont_buy": "Adverse fiscal recommendation. The purchase presents high redundancy and marginal utility. Capital preservation is advised.",
        "challenge_intro": "Counter-factual scenario analysis: affirmative arguments supporting capital deployment:",
    },
}


def get_personality_profile(personality: str) -> Dict[str, str]:
    """Returns profile dictionary fallback to Best Friend."""
    return PERSONALITY_PROFILES.get(personality, PERSONALITY_PROFILES["Best Friend"])


def format_personality_explanation(
    personality: str,
    recommendation: str,
    product_name: str,
    score: float,
    impulse_prob: float,
    reasons: List[str],
    positive_factors: List[str],
) -> str:
    """Renders the comprehensive explanation in the selected persona voice."""
    profile = get_personality_profile(personality)

    rec_key = {
        "BUY NOW": "buy_now",
        "CONSIDER": "consider",
        "WAIT 7 DAYS": "wait_7days",
        "DON'T BUY": "dont_buy",
    }.get(recommendation, "consider")

    persona_quote = profile.get(rec_key, profile["consider"])

    reason_bullet = "\n".join([f"• {r}" for r in reasons[:3]]) if reasons else "• Balanced considerations."
    positive_bullet = "\n".join([f"• {p}" for p in positive_factors[:3]]) if positive_factors else "• Discretionary utility."

    explanation = (
        f"{persona_quote}\n\n"
        f"Key Assessment Points for '{product_name}':\n"
        f"{reason_bullet}\n\n"
        f"Points in Favor:\n"
        f"{positive_bullet}"
    )

    return explanation
