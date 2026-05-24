# Student Claim And Wrapper

## Goal

Validate the visible student claim flow and wrapper shell.

## Steps

1. Open `/labs/hlf/`.
2. Confirm the route redirects to `/labs/hlf/claim`.
3. Let the claim flow complete and confirm the wrapper lands on
   `/labs/hlf/c/<uuid>/`.
4. Confirm the page shows the student role, school name, and links to
   exercises, explorer, governance, and `Your Console`.
5. Check console errors and network failures for the landing route and
   wrapper route.

## Expected Result

- the student gets a claim
- the wrapper renders the student-specific context
- no unexplained browser errors appear
