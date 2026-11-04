Custom Alias - Let User Choose Their Own Short CodeNormal shorten gives a random code like a1B2c3. Nobody can remember it.Custom Alias lets user choose it. 

Like tynly.in/my-youtube instead of tynly.in/a1B2c3.That is why Bitly, TinyURL all have this feature. People remember words, not random letters.

How it worksIn /shorten, we add one new optional input: custom_code.If user sends it, we use that code.

If user does not send it, we keep old behaviour and generate random code.So old links keep working, new feature is just extra.

4 Rules for Custom Alias

1. Format Rule
Only allow letters, numbers, - and _.
Why? Because URL cannot have spaces or symbols like ! @ # $ %. If user types my code!!, browser will break the link. So we reject it early.

2. Length Rule
Must be 3 to 30 characters.
Why? 1 or 2 letters are too easy to guess and will finish fast. More than 30 is not short anymore. It defeats the purpose of short link.

3. Reserved Words Rule
Block words like health, docs, stats, shorten.
Why? This is our catch-all lesson again. GET /health is above GET /{short_code}. So if user creates a link called health, they can never open it. /health will always win. So we block those words to avoid confusion.

4. Uniqueness Rule
One code = One link.
If my-youtube is already taken, we cannot give it to second person. We return 409 Already Taken. User has to choose another. This is same as username on Instagram, two people cannot have same username.What to test in mindWith custom code -> should create that exact linkSame custom code again -> should say already takenCustom code = health -> should say reservedCustom code with space or !! -> should say invalidNo custom code -> should still give random codeOne line to remember:Custom alias is just a choice. Random is fallback. But reserved words and duplicate check are compulsory, otherwise routing breaks.