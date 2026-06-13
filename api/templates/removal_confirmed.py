"""Email template for confirmed removal notifications."""

REMOVAL_CONFIRMED_TEMPLATE = {
    "subject": "✅ Data Removal Confirmed - {broker_name}",
    "body_text": """\
Hi {user_name},

Good news! Your data has been successfully removed from {broker_name}.

Details:
  Profile: {profile_name}
  Broker: {broker_name}
  Removed at: {timestamp}

The listing is no longer accessible on their platform. We will continue to monitor for re-listings.

Thank you for using OpenDataRemoval.
""",
    "body_html": """\
<!DOCTYPE html>
<html>
<head><style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
  .container { max-width: 600px; margin: 0 auto; background: #fff; border-radius: 8px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .header { color: #22c55e; font-size: 24px; margin-bottom: 16px; }
  .detail { margin: 8px 0; color: #374151; }
  .label { font-weight: 600; color: #6b7280; }
  .footer { margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 14px; }
</style></head>
<body>
  <div class="container">
    <div class="header">✅ Data Removal Confirmed</div>
    <p>Your data has been successfully removed from <strong>{broker_name}</strong>.</p>
    <div class="detail"><span class="label">Profile:</span> {profile_name}</div>
    <div class="detail"><span class="label">Broker:</span> {broker_name}</div>
    <div class="detail"><span class="label">Removed at:</span> {timestamp}</div>
    <p>We will continue to monitor for re-listings.</p>
    <div class="footer">Thank you for using OpenDataRemoval.</div>
  </div>
</body>
</html>
""",
    "variables": ["user_name", "profile_name", "broker_name", "timestamp"],
}