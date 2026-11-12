# Before the first class

Checks that can only happen on a day that has not come: on the real cloud host, in a real browser, in a real class,
or on a Mac. Everything a computer here could prove is already proved by tests; these are the rest. Work that waits
for such a day goes on this page, not on `docs/follow-ups.md`.

How to use it: do a step, then write the result in that step's **Result** line (date, who, host, pass or fail, and
the numbers). Commit the page with the result. A step that fails becomes a fix, and the step stays here until it
passes.

Lab hosting is decided (owner, 8 Nov 2026): one shared host per class, the cloud by default and the classroom
server as the offline fallback. Self-study on a student's own computer goes through the student launcher by default,
with the student VM kept as the offline option (owner, 11 Nov 2026). The steps below are for the cloud host. The deploy itself is in `dynamic-labs/README.md`, "Cloud (public VM with HTTPS)".

## On the real cloud host

Do these on the host after `sudo ./deploy-cloud.sh --domain <domain> --max-student-capacity 40` and
`./lab-manager.sh start all`, from the `dynamic-labs` folder. `<domain>` is the `--domain` you deployed with; it is
saved in `.runtime/cloud-domain.txt`.

### 1. Measure the host

The host size in `dynamic-labs/README.md` ("Host size for a class") is a local estimate: it was measured on the
course desktop (Docker Desktop, 20 CPUs, 15.6 GiB) on 9 Nov 2026, not on a cloud host. Rerun the measurement on the
real host before the first cloud class.

On a cloud host the router answers plain `http://127.0.0.1` with a redirect to HTTPS, which the script cannot
follow, so give it the domain:

```bash
python3 scripts/measure-seats.py --seats 20 --base-url https://<domain> bitcoin consensus hlf
python3 scripts/measure-seats.py --seats 40 --burst --base-url https://<domain> bitcoin hlf
```

The first command starts 20 idle seats of each lab, reads `docker stats`, prints each lab's per-seat CPU and RAM and
the shared containers' total, and stops the lanes it started. The second has all 40 seats act at the same moment,
the way a class does when the instructor says "go". Both sign in with
`.runtime/instructor-credentials.txt`, so run them on the host. Bitcoin was never run at 40 seats on the desktop, so
that figure will be new.

A pass: no seat fails, and the numbers are in line with the desktop's. On the desktop (9 Nov 2026) one Fabric seat
was 85 MiB, one Bitcoin seat 77 MiB, one Ethereum seat 37 MiB, one consensus or P2P trust seat 17 MiB, and every lab
started with no student lanes took 5.0 GiB. In the bursts the 20 Bitcoin seats each waited 23 s to 94 s (median
47 s), the 40 Fabric seats 14 s to 16 s with every invoke succeeding, and the 40 Ethereum seats 4 s to 6 s. The
recommended host holds: 8 vCPU, 16 GiB RAM, 100 GB SSD for 20 seats; 16 vCPU, 32 GiB RAM, 150 GB SSD for 40. If the
real host's figures are worse, change the recommendation.

Where to write it: the Result line below, and the table and recommended host in `dynamic-labs/README.md` ("Host
size for a class"), so the table says "measured on a cloud host" with its date.

**Result:** not run yet.

### 2. The class code in a real browser

The class-pass cookie is set on the parent domain (`CLASS_PASS_COOKIE_DOMAIN`, `dynamic-labs/lab-manager.sh`), so
one entry should cover the main host and the `explorer.`, `tokens.`, `dex.` and `dex-l2.` hosts.
`dynamic-labs/tests/test_class_gate.py`, `test_class_gate_deploy.py` and `test_lane_service_class_gate.py` simulate
that but cannot prove that a real browser shares the cookie.

A person, in a browser that has never visited the host (a private window works), does this:

1. Read the class code in `.runtime/instructor-credentials.txt` ("Class Code") on the host.
2. Open `https://<domain>/` in the browser. It must go to the class code page (`/class/`) over HTTPS.
3. Enter the code. It must return to the page that was asked for.
4. Without entering the code again, open `https://explorer.<domain>/`, `https://tokens.<domain>/`,
   `https://dex.<domain>/` and `https://dex-l2.<domain>/`.

A pass: all four open the lab itself and none asks for the code again. A fail: any of them shows the code page
again. Check the cookie in the browser's developer tools (its Domain should be `<domain>`, or `.<domain>`).

Where to write it: the Result line below.

**Result:** not run yet.

### 3. Certificate renewal

The certificate lasts 90 days and renews itself through the router's challenge path.
`dynamic-labs/tests/test_acme_challenge.py` checks the config, not Let's Encrypt.

```bash
sudo certbot renew --dry-run
```

A pass: certbot ends with "Congratulations, all simulated renewals succeeded" and lists the lab certificate
(named for `<domain>`). A fail names the challenge it could not reach; check ports 80 and 443 and that the router is
up (`./lab-manager.sh status all`). A host first deployed before 9 Nov 2026 got its certificate with `--standalone`:
rerun `sudo ./deploy-cloud.sh --domain <domain>` once first (the router stops for about a minute).

Where to write it: the Result line below.

**Result:** not run yet.

## In the first real class

### 4. The exchange and bridge lab (day 4)

The lab has not been tried with a real class. A scripted 40-seat run (1 Nov 2026) sent every seat's 0.1 ETH swap
into one L1 block: 3 landed and 37 reverted at the page's 99% minimum ("too little received"). Re-quoting and
sending again, about 3 seats land per block, so all 40 took 14 blocks (about 3 minutes) and the price fell from
about 1,999 to 1,714 cUSD per WETH. The relayer finalized 40 deposits from one L1 block in about 25 s each, and
every seat found its L2 transaction. The swap page now explains a revert and asks for a new quote.

The owner kept the pool and the minimum as they are (1 Nov 2026: "Keep as a slippage lesson"). The instructor
answers (`dynamic-labs/dex/quizes/INSTRUCTOR_ANSWERS.md`) warn to expect it. So most first swaps failing is the
lesson working, not a fault.

What to watch when the whole class swaps at once:

- Most first swaps revert with "too little received", and the page tells the student to ask for a new quote and send
  again. A pass: every student's swap lands within a few tries (about 3 seats land per block, so a class of 40 needs
  about 14 blocks, about 3 minutes), and the instructor can point at the price falling as swaps land.
- A bridge deposit finalizes on L2 in about 20 s to 40 s. A pass: every student finds their L2 transaction. A fail:
  a deposit still waiting after two minutes (the relayer, Account 7, is not sending).
- The students read the same pool, so a student whose swap paid less than the quote had someone else's swap land
  first. That is expected.

Where to write it: the Result line below, with the class size, how many blocks the swaps took and any seat that
could not finish. If the class shows something the scripted run did not, fix it, and say so here.

**Result:** not run yet.

## On a Mac

### 5. Start and Stop Course Labs with Docker Desktop

What a computer here already proves: the release's `mac` job (`.github/workflows/student-release.yml`) runs
`Start-Course-Labs.command` and `Stop-Course-Labs.command` with macOS's own `/bin/bash` and tools on a GitHub Intel
Mac, against a Colima Docker engine, checks the control page answers, and shellchecks both; unit tests
(`student-launcher/control/tests/test_wrappers.py`) cover their macOS branches (`open`, `open -a Docker`). What it
cannot prove: GitHub's Apple silicon Macs cannot run Docker (no nested virtualization, its runner docs as of
10 Nov 2026), and no runner has Docker Desktop, Finder or Gatekeeper. Those need a person with a Mac.

On an Apple silicon Mac (M1 or newer; an Intel Mac too, if one is to hand) with Docker Desktop installed and quit,
and no `course-launcher` container (`docker ps -a`):

1. Download `Course-Labs.zip` from the latest release
   (`https://github.com/astevegreen/blockchain-technology-course/releases/latest`) in Safari, and double-click it.
2. Follow the student guide's Mac steps (`blockchain-course/run-labs.qmd`, "Mac"): double-click **Start Course
   Labs**, press **Done**, then **Open Anyway** in Privacy & Security, the password, and **Open**.
3. Watch the Terminal window. A pass: it prints "Starting Docker Desktop. This can take a minute...", Docker Desktop
   starts by itself, then "Getting the latest course labs...", and the browser opens `http://127.0.0.1:8470/` with
   the labs listed. A fail: "permission denied" or "cannot be executed" (the zip lost the executable bit), any
   other message from the guide's table of messages, or no browser.
4. Start one lab from the page (the Consensus Lab is a small one) and open it. A pass: its page opens.
5. Double-click **Stop Course Labs**. A pass: it prints "The course labs are stopped..." and `docker ps -a` shows no
   `course-launcher` and no lab running.
6. Double-click **Start Course Labs** again with Docker Desktop running. A pass: no warning this time, and the page
   opens within a minute.

Where to write it: the Result line below, with the Mac's chip, macOS version and Docker Desktop version. A fail is
fixed in `student-launcher/` (the `.command` files stay byte-identical to the `.sh` ones), and the step stays here
until it passes.

**Result:** not run yet.
