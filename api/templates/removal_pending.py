"""Email template for pending removal notifications."""

REMOVAL_PENDING_TEMPLATE = {
    "subject": "⏳ Removal Requested - {broker_name}",
    "body_text": """\
Hi {user_name},

A removal request has been submitted for your profile on {broker_name}.

Details:
  Profile: {profile_name}
  Broker: {broker_name}
  Requested at: {timestamp}

We are waiting for confirmation from the broker. You will receive another email once the removal is processed.

Thank you for using OpenDataRemoval.
""",
    "body_html": """\
<!DOCTYPE html>
<html>
<head><style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
  .container { max-width: 600px; margin: 0 auto; background: #fff; border-radius: 8px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .header { color: #f59e0b; font-size: 24px; margin-bottom: 16px; }
  .detail { margin: 8px 0; color: #374151; }
  .label { font-weight: 600; color: #6b7280; }
  .footer { margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 14px; }
</style></head>
<body>
  <div class="container">
    <div class="header">⏳ Removal Requested</div>
    <p>A removal request has been submitted for your profile on <strong>{broker_name}</strong>.</p>
    <div class="detail"><span class="label">Profile:</span> {profile_name}</div>
    <div class="detail"><span class="label">Broker:</span> {broker_name}</div>
    <div class="detail"><span class="label">Requested at:</span> {timestamp}</div>
    <p>We are waiting for confirmation from the broker. You will receive another email once processed.</p>
    <div class="footer">Thank you for using OpenDataRemoval.</div>
  </div>
</body>
</html>
""",
    "variables": ["user_name", "profile_name", "broker_name", "timestamp"],
}