import json
from pathlib import Path

repo = Path(r"C:/Users/Admin/Desktop/Working/GitHub_Overnight_Study/espocrm")
composer = json.loads((repo / "composer.json").read_text(encoding="utf-8"))
lead = json.loads((repo / "application/Espo/Modules/Crm/Resources/metadata/entityDefs/Lead.json").read_text(encoding="utf-8"))
scope = json.loads((repo / "application/Espo/Modules/Crm/Resources/metadata/scopes/Lead.json").read_text(encoding="utf-8"))
capture = (repo / "application/Espo/Tools/LeadCapture/CaptureService.php").read_text(encoding="utf-8")
api = (repo / "application/Espo/Tools/LeadCapture/Api/PostForm.php").read_text(encoding="utf-8")
confirmation = (repo / "application/Espo/Tools/LeadCapture/ConfirmationSender.php").read_text(encoding="utf-8")

checks = {
    "license_is_AGPL_3_or_later": composer.get("license") == "AGPL-3.0-or-later",
    "lead_status_pipeline_present": all(s in lead["fields"]["status"]["options"] for s in ["New", "Assigned", "In Process", "Converted", "Recycled", "Dead"]),
    "email_marked_personal_data": lead["fields"]["emailAddress"].get("isPersonalData") is True,
    "phone_marked_personal_data": lead["fields"]["phoneNumber"].get("isPersonalData") is True,
    "scope_duplicate_fields_include_name_email": set(scope.get("duplicateCheckFieldList", [])) >= {"name", "emailAddress"},
    "capture_route_checks_captcha_and_calls_service": "X-Captcha-Token" in api and "captureForm" in api,
    "capture_service_has_email_phone_dedupe_and_optin": all(s in capture for s in ["findLeadDuplicates", "emailAddress", "phoneNumber", "OptInConfirmation", "skipOptInConfirmationIfSubscribed"]),
    "confirmation_sender_sends_after_confirmation_token": all(s in confirmation for s in ["Confirm Opt-In", "UniqueId", "emailSender"]),
}
for name, passed in checks.items():
    print(f"{'PASS' if passed else 'FAIL'} {name}")
failed = [name for name, passed in checks.items() if not passed]
print(f"RESULT: {len(checks)-len(failed)}/{len(checks)} static source assertions passed")
if failed:
    raise SystemExit(1)
