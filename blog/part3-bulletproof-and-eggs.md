# Poetry Phone — Part 3: Kid-Proofing and Easter Eggs

The Poetry Phone worked. Pick up, dial, hear a poem, hang up. Beautiful.

Then I remembered where it was going: the O, Miami Poetry Festival. An outdoor event in Miami. Where children exist.

Kids don't use phones the way adults do. Kids pick up the handset and slam it down. They mash every button at once. They dial half a number, get distracted by a dog, and walk away with the handset dangling off the table. They hold down the 5 key for thirty seconds to see what happens.

The phone needed to survive all of this without anyone power-cycling it.

## The Threat Model: Children

I sat down and listed every way a kid could break the phone:

1. **Walk away mid-dial.** The phone loops forever: dial tone → timeout → busy → dial tone → timeout → busy. Nobody hangs up. Nobody resets it. The phone is stuck.
2. **Slam the handset.** The hook switch bounces, causing false hangup/pickup events. The state machine gets confused.
3. **Hold a key down.** The key release function blocks waiting for the key to come up. If it never comes up, the watchdog timer fires and reboots the Pico mid-call.
4. **Mash buttons rapidly.** Digits pile up past 10. The phone doesn't know what to do with an 18-digit number.
5. **The code crashes.** Any unhandled exception kills the main loop. The phone is dead until someone unplugs it.

Every one of these happened during testing.

## The Fixes

### Watchdog Timer

The RP2040 has a hardware watchdog timer. You start it with a timeout (8 seconds), and if your code doesn't "feed" it within that window, the chip hard-reboots. It's a last resort — if the code hangs in a way no software can recover from, the hardware saves you.

```python
from machine import WDT
wdt = WDT(timeout=8000)

while True:
    wdt.feed()  # I'm still alive
    # ... do stuff ...
```

But there's a catch. The main loop has blocking calls that can run for up to 8 seconds — `get_key_timeout(8000)` waits for a keypress during dialing. If the watchdog isn't fed during those waits, it reboots the Pico mid-conversation.

The fix: feed the watchdog inside every blocking loop, not just at the top of the main loop.

```python
def get_key_timeout(timeout_ms):
    deadline = utime.ticks_add(utime.ticks_ms(), timeout_ms)
    while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
        if wdt:
            wdt.feed()  # keep the watchdog happy while waiting
        # ... scan keypad ...
```

Same for `wait_with_hangup_check()` and `wait_release()`.

### Crash Recovery

The entire state machine is wrapped in try/except. If anything throws an exception — UART glitch, memory error, anything — the phone resets to idle and keeps running.

```python
while True:
    if wdt:
        wdt.feed()

    try:
        # ... entire state machine ...
    except Exception as e:
        print("!!! ERROR: {}".format(e))
        try:
            stop_audio()
        except:
            pass
        state = STATE_IDLE
        number = ""
        utime.sleep_ms(1000)
```

The 1-second sleep prevents a tight crash loop from burning CPU. The phone just quietly resets and waits for the next handset lift.

### Off-Hook Hard Timeout

If a kid walks away with the handset off the hook, the phone used to loop: dial tone → 30s timeout → busy signal → dial tone → forever. Now there's a 2-minute hard timeout. After 2 minutes off-hook with no completed call, the phone goes silent and waits. It requires a hangup and re-lift to start again.

```python
OFF_HOOK_TIMEOUT = 120000  # 2 minutes

if utime.ticks_diff(utime.ticks_ms(), off_hook_start) > config.OFF_HOOK_TIMEOUT:
    print("[off-hook timeout]")
    stop_audio()
    state = STATE_IDLE  # not OFF_HOOK — breaks the loop
```

The key insight: go to IDLE, not OFF_HOOK. Going back to OFF_HOOK would start a new dial tone, which starts the loop over. Going to IDLE means silence until someone actually hangs up and picks up again.

### Debounced Hangup

The original `check_hangup()` did a single pin read. Slamming the handset causes the hook switch to bounce — briefly reading "off-hook" during a slam-down. One bad read in the middle of a poem could cancel playback.

Now it requires 3 consecutive on-hook reads with 5ms gaps:

```python
def check_hangup():
    for _ in range(3):
        val = hook_pin.value()
        if not ((val == 1) != config.HOOK_ACTIVE_HIGH):
            return False  # one read says still off-hook
        utime.sleep_ms(5)
    return True
```

15ms total latency. Imperceptible to humans. Immune to bounce.

### Stuck Key Protection

The `wait_release()` function blocks until all keys are released. If a key is stuck (held down, or a noisy row), it used to block forever. Now it has a 2-second timeout and returns `True` to signal "stuck key" — the caller resets to dial tone instead of accepting the phantom key.

```python
def wait_release():
    deadline = utime.ticks_add(utime.ticks_ms(), 2000)
    while clean < 5:
        if utime.ticks_diff(deadline, utime.ticks_ms()) <= 0:
            return True  # stuck key
        # ... scan for release ...
    return False
```

### The Small Stuff

- **Digit cap:** More than 10 digits? Busy signal, reset. No buffer overflow from button mashing.
- **Heartbeat LED:** The Pico's onboard LED (GP25) toggles every loop. Blinking = alive. Solid or off = frozen. At the festival, one glance tells you if the phone is running.
- **Boot chime:** A 500ms dial tone burst on power-up. If the watchdog reboots the Pico, you hear it come back.
- **gc.collect():** MicroPython has a small heap. Running `gc.collect()` every loop iteration prevents memory fragmentation over hours of continuous use.
- **Random seed:** `random.seed(utime.ticks_us())` at boot so the first poem isn't always the same after a power cycle.

## Easter Eggs

The phone was functional. Now it needed personality.

The phonebook maps specific numbers to specific audio. Dial 867-5309 and you get a specific poem — because it's Jenny's number, and we all know Jenny. But what about other famous numbers?

| Dial | What You Hear |
|------|--------------|
| **867-5309** | Jenny Munaweera's poem (Tommy Tutone, obviously) |
| **555-2368** | "Who are you going to call?... A poet?" (Ghostbusters) |
| **555-1212** | Ericka's poem (classic directory assistance number) |
| **324-8811** | "At the tone, the time will be... poetry o'clock" (Miami's old time-of-day number) |
| **777-3456** | Poemafone — a Moviefone parody featuring P. Scott Cunningham in *A Poet Stuck in Chicago* |

All numbers also work with the 305 area code: 305-867-5309, 305-777-3456, etc.

The special codes play custom messages generated with ElevenLabs TTS. Dial 411 for directory assistance and you get an actual explanation of the phone, plus hints about the Easter eggs. Dial 911 and you're told "This is not a real phone — please dial 9-1-1 on a real phone." Dial 611 and all representatives are busy reading poetry.

My favorite is the Poemafone (777-FILM). The original Moviefone — you'd call to hear showtimes before the internet existed. Our version:

> *"Now showing: P. Scott Cunningham in... A Poet Stuck in Chicago. A documentary. One poet. One city. Zero flights home. He came for a fresh start. He stayed because the house needed work. The winters stayed because they always do. Critics are calling it... Remarkably cold. Aggressively cold. Why is he still there?"*

> *"Showtimes are: always. Because unlike movies, poems never stop playing. They're showing right now. In your head. See?"*

> *"No refunds. No concessions. Unlimited poems."*

## The Test Suite

Before any of this went to the festival, it needed tests. All 169 of them.

The challenge: the code runs on MicroPython with real hardware. The tests run on desktop Python with mocks. We built a `PhoneSimulator` class that replicates the state machine logic with injectable mocks for time, pins, audio, and the DFPlayer. A separate set of tests validates that every file referenced in config.py actually exists on the SD card — if you add a phonebook entry but forget the MP3, the tests catch it.

```
169 passed in 0.06s
```

The SD card validation tests are my favorite safety net. They check:
- Every SFX number in config has a matching MP3 in `/01/`
- Every phonebook entry has a matching MP3 in `/02/`
- `RANDOM_COUNT` matches the actual file count in `/03/`
- No orphan files in any folder

Add a new Easter egg to the phonebook, forget to copy the audio file, and your CI pipeline tells you before the festival.

## What I Learned

1. **Design for the worst user, not the best one.** A phone at an art festival isn't used by engineers. It's used by six-year-olds who think the handset is a hammer.

2. **Hardware watchdog is non-negotiable for unattended devices.** Software recovery (try/except) handles 99% of crashes. The watchdog handles the 1% where your code is stuck in a blocking call and can't recover.

3. **Feed the watchdog in every blocking loop.** Not just at the top of the main loop. If any function can block for longer than your watchdog timeout, feed it there too.

4. **`machine.UART()` on RP2040 claims default pins silently.** Always pass explicit `tx` and `rx`. This one line of missing code caused days of intermittent keypad failures. See [Part 2](part2-dfplayer-audio.md) for the full story.

5. **Easter eggs make art installations memorable.** Nobody remembers "I dialed a number and heard a poem." Everyone remembers "I dialed 777-FILM and got a fake Moviefone about a poet stuck in Chicago."

The Banana Poem Phone is ready for O, Miami. Pick up the handset. Dial a number. Any number. You'll hear a poem. And if you dial the right number, you might hear something you didn't expect.

---

*This project is built for the [O, Miami Poetry Festival](https://www.omiami.org/). The full source code is available on [GitHub](https://github.com/MarioCruz/OMiamiPhone). Created by Mario The Maker.*
