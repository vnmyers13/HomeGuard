"""Email template for scan completion notifications."""

SCAN_COMPLETE_TEMPLATE = {
    "subject": "📋 Scan Complete - {profile_name}",
    "body_text": """\
Hi {user_name},

Your scan for {profile_name} has completed.

Results:
  Total brokers scanned: {total_brokers}
  Listings found: {listings_found}
  Removals requested: {removals_requested}

You can view the full report in your OpenDataRemoval dashboard.

Thank you for using OpenDataRemoval.
""",
    "body_html": """\
<!DOCTYPE html>
<html>
<head><style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
  .container { max-width: 600px; margin: 0 auto; background: #fff; border-radius: 8px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .header { color: #3b82f6; font-size: 24px; margin-bottom: 16px; }
  .stat { display: inline-block; background: #f3f4f6; border-radius: 6px; padding: 12px 16px; margin: 4px; text-align: center; }
  .stat-value { font-size: 24px; font-weight: 700; color: #1f2937; }
  .stat-label { font-size: 12px; color: #6b7280; text-transform: uppercase; }
  .footer { margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 14px; }
</style></head>
<body>
  <div class="container">
    <div class="header">📋 Scan Complete</div>
    <p>Your scan for <strong>{profile_name}</strong> has completed.</p>
    <div style="margin: 16px 0;">
      <div class="stat"><div class="stat-value">{total_brokers}</div><div class="stat-label">Brokers Scanned</div></div>
      <div class="stat"><div class="stat-value">{listings_found}</div><div class="stat-label">Listings Found</div></div>
      <div class="stat"><div class="stat-value">{removals_requested}</div><div class="stat-label">Removals Requested</div></div>
    </div>
    <p>You can view the full report in your OpenDataRemoval dashboard.</p>
    <div class="footer">Thank you for using OpenDataRemoval.</div>
  </div>
</body>
</html>
""",
    "variables": ["user_name", "profile_name", "total_brokers", "listings_found", "removals_requested"],
}