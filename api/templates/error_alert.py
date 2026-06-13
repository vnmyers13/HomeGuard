"""Email template for error alert notifications."""

ERROR_ALERT_TEMPLATE = {
    "subject": "⚠️ Error Alert - {broker_name}",
    "body_text": """\
Hi {user_name},

An error occurred while processing your request for {broker_name}.

Details:
  Profile: {profile_name}
  Broker: {broker_name}
  Error: {error_message}
  Occurred at: {timestamp}

Our team has been notified. We will retry automatically or you can manually trigger a re-scan from your dashboard.

Thank you for using OpenDataRemoval.
""",
    "body_html": """\
<!DOCTYPE html>
<html>
<head><style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
  .container { max-width: 600px; margin: 0 auto; background: #fff; border-radius: 8px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .header { color: #ef4444; font-size: 24px; margin-bottom: 16px; }
  .detail { margin: 8px 0; color: #374151; }
  .label { font-weight: 600; color: #6b7280; }
  .error { background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 12px; margin: 12px 0; color: #991b1b; }
  .footer { margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 14px; }
</style></head>
<body>
  <div class="container">
    <div class="header">⚠️ Error Alert</div>
    <p>An error occurred while processing your request for <strong>{broker_name}</strong>.</p>
    <div class="detail"><span class="label">Profile:</span> {profile_name}</div>
    <div class="detail"><span class="label">Broker:</span> {broker_name}</div>
    <div class="error">{error_message}</div>
    <div class="detail"><span class="label">Occurred at:</span> {timestamp}</div>
    <p>We will retry automatically, or you can manually trigger a re-scan from your dashboard.</p>
    <div class="footer">Thank you for using OpenDataRemoval.</div>
  </div>
</body>
</html>
""",
    "variables": ["user_name", "profile_name", "broker_name", "error_message", "timestamp"],
}