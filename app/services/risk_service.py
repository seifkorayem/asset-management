from app.models import Asset


def calculate_asset_risk(asset: Asset):
    score = 0
    reasons = []

    # Expired/Stale certificate
    if asset.type == "certificate" and asset.status == "stale":
        score += 40
        reasons.append("Expired certificate (+40)")

    # SSH service
    if asset.type == "service" and "ssh" in asset.value.lower():
        score += 20
        reasons.append("SSH service (+20)")

    # Old technology
    old_tech = [
        "windows xp",
        "windows 7",
        "tls 1.0",
        "tls1.0",
        "apache 2.2",
        "php 5",
        "python2",
        "python 2"
    ]

    value = asset.value.lower()

    for tech in old_tech:
        if tech in value:
            score += 30
            reasons.append(f"Old technology ({tech}) (+30)")
            break

    return {
        "asset_id": asset.id,
        "risk_score": score,
        "reasons": reasons
    }