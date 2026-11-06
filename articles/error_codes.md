3 Bugs That Broke My URL Shortener's Expiry

I built a URL shortener with FastAPI + SQLite. The expiry feature with expires_in_days: -1 should return 410 Gone, but instead it gave 307 Redirect, then 500 Internal Server Error. Here are the 3 bugs I found, in order.


Bug 1: Saving the Wrong Variable
Symptom: Link with expires_in_days: -1 still redirected with 307 instead of 410.
Wrong code:pythonexpiry = None

if req.expires_in_days:
    expiry = datetime.now(timezone.utc) + timedelta(days=req.expires_in_days)


new_link = Link(short_code=c_code, long_url=req.long_url, expires_at=req.expires_in_days)Problem: I calculated the correct datetime in expiry, but then saved req.expires_in_days which is just the int -1. The expires_at column expects a DateTime, not an int.

Fix:pythonnew_link = Link(short_code=c_code, long_url=req.long_url, expires_at=expiry)Lesson: An unused variable is a red flag. If you create expiry but never use it, something is wrong. Also, check types: DateTime column should never get an int.

Bug 2: Old Bad Data in the Database
Symptom: After fixing Bug 1, the old link still failed.
Problem: The old links created before the fix still had expires_at = -1 stored in the DB. Fixing the code doesn't fix data already saved.
Fix: Delete the .db file, restart the server, and create a fresh link to test.
Lesson: When you fix a bug that writes bad data, you have to throw away the old bad data too.


Bug 3: Naive vs Aware Datetimes - SQLite Strips Timezone
Symptom: 500 Internal Server Error with this error:javascriptTypeError: can't compare offset-naive and offset-aware datetimesProblem:
I saved datetime.now(timezone.utc) - this is aware, it has timezone info.SQLite doesn't store timezone, it strips it.When I load it back, 

link.expires_at is naive, no timezone.Python refuses to compare naive < aware.Wrong code:pythonif link.expires_at is not None and link.

expires_at < datetime.now(timezone.utc):Fix:pythonif link.expires_at is not None:
    expires = link.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Link expired")Lesson: If you use SQLite + datetimes, always normalize on read. Check tzinfo is None and add UTC back.


HTTP Codes I UsedCodeMeansWhen201CreatedNew short link made307Temporary RedirectRedirect to long URL404Not FoundShort code doesn't exist410GoneLink existed but expired500Server ErrorCode crashed, like the datetime compareDebugging Method That Worked
Don't guess. Trace backwards:
Start from wrong output - 307 instead of 410 means the expiry if never became True.Ask what value would make that happen - expires_at must be None or not a past datetime.Go to where that value is created - the /shorten endpoint.Print the value - print(expires_at, type(expires_at)) would have shown -1 instead of a datetime.