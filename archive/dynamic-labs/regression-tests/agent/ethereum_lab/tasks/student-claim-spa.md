# Task: Student Claim And SPA Shell

Goal:

- validate the student entry flow from `/labs/ethereum_lab/` through
  claim and into the SPA shell
- capture browser-side JavaScript and network issues on initial load

Steps:

1. Open `/labs/ethereum_lab/`.
2. Confirm the route claims a lane instead of failing immediately.
3. Wait through the startup page until the SPA shell loads.
4. Confirm the app is the Ethereum trainer and not a blank or broken
   page.
5. Confirm the SPA can reach `/labs/ethereum_lab/api/config.json`.
6. Capture console logs and network failures for the claim and shell
   load.

Pass criteria:

- claim succeeds
- staging page clears
- student SPA shell renders
- runtime config loads
- no unexplained JavaScript or network failures remain

