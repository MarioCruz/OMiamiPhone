# Poetry Phone — Shopping List

Everything you need to buy, with search terms and sourcing tips.

## Amazon / Online

| # | Item | Search Term | Qty | ~Price | Notes |
|---|------|------------|-----|--------|-------|
| 1 | DFPlayer Mini | "DFPlayer Mini MP3 module" | 1 | $2-6 | **[WWZMDiB YX5200 DFPlayer Mini on Amazon](https://www.amazon.com/WWZMDiB-YX5200-DFPlayer-Supporting-Arduino/dp/B0CH2WZT5Q)** — YX5200 chip (preferred). Get a multi-pack for spares. |
| 2 | microSD card | "microSD 16GB" or "microSD 32GB" | 1 | $5-8 | Must be ≤32GB and formatted FAT32. Brand doesn't matter — even the cheapest works. You probably have one in a drawer. |
| 3 | 1K resistor | "1K ohm resistor assortment" | 1 | $0.05 | Buy a resistor kit if you don't have one (~$7 for a full assortment). Only need a single 1K. |
| 4 | Jumper wires | "dupont jumper wires male-to-male" | ~8 | $2-5 | Or use any hookup wire. Need about 8 connections total. |
| 5 | Breadboard | "half-size breadboard" | 1 | $2-4 | Optional — only if you want to prototype before soldering. |

## Thrift Store / eBay / Facebook Marketplace

| # | Item | What to Look For | Qty | ~Price | Notes |
|---|------|-----------------|-----|--------|-------|
| 6 | Vintage phone | Desk phone with handset + cradle | 1 | $5-20 | Needs: (a) handset with earpiece speaker, (b) hook switch in the cradle. Corded desk phones from the 80s-90s are ideal. Trim phones, rotary phones, or novelty phones all work. |
| 7 | Phone cord | RJ11 handset cord | 1 | $1-3 | Usually comes with the phone. You'll cut one end and wire to the DFPlayer SPK1/SPK2. |

## What to Check When Buying the Phone

- **Earpiece**: Unscrew the earpiece cap on the handset. You should see a small round speaker (typically 8-ohm). If it's there, you're good.
- **Hook switch**: Press the cradle buttons/lever. You should feel a click. Use a multimeter on continuity mode across the two hook switch wires — it should beep when the handset is down and stop when you lift it (or vice versa).
- **Wires**: The handset cord typically has 4 wires (RJ11). You only need 2 for the earpiece. The other 2 are for the microphone (not used).

## Already Owned (No Purchase Needed)

| Item | Status |
|------|--------|
| Raspberry Pi Pico (RP2040) | Have it — device ID e660c062136d6e27 |
| 3x4 membrane phone keypad | Have it — wired to GP0-GP6 |
| USB cable (micro-USB) | Have it — for programming via mpremote |
| Computer with mpremote | Have it — mpremote v1.27.0 via Homebrew |

## Optional / Nice-to-Have

| Item | Search Term | ~Price | Why |
|------|------------|--------|-----|
| USB wall adapter (5V 1A+) | "USB wall charger 5V" | $5-8 | Run the phone standalone without a laptop |

