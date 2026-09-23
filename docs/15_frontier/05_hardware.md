# What changed in robot arm hardware, and when

This document records the hardware events of roughly the last two years: which
arms, hands, sensors and computers appeared, which ones changed price, which
companies were bought, and which announcements have still produced nothing you
can buy. It is the document to read before spending money.

It is deliberately an events document. It does not try to explain why hardware
moves in the direction it moves, because
[what is changing in robot manipulation](../10_one-arm-training/05_what-is-changing.md)
already does that, and the two overlap on purpose. If you want the mechanism,
read that one. If you want to know what happened and on what date, read this one.

It is also not a catalogue. [Grippers and the hardware around
them](../07_gripping/02_grippers-and-hardware.md) already gives the payloads,
strokes, forces and drivers for every gripper family, and this document links to
it rather than repeating it. Where the two documents touch, that one tells you
what a product does and this one tells you when it arrived and what it replaced.

## Who this is for

Someone with a budget and a decision to make. A person deciding whether to buy a
cheap arm or a capable one, a lab deciding whether last year's quote is still
good, or anyone who has read an announcement and wants to know whether the thing
in it exists.

Every figure below was read from the manufacturer's own page, its own online
store, or its own repository, fetched in September 2026, and the link is given so
you can check it. Historical prices come from dated snapshots in the Internet
Archive or from dated commits in a public repository, and those links are given
too. Where a vendor publishes no price, the document says so instead of quoting a
reseller. Where a page could not be read at all, the document says that as well.

## Contents

1. [How to read this document](#1-how-to-read-this-document)
2. [Collaborative and industrial arms](#2-collaborative-and-industrial-arms)
3. [Research and low-cost arms](#3-research-and-low-cost-arms)
4. [Humanoid arms and hands](#4-humanoid-arms-and-hands)
5. [Grippers and multi-finger hands](#5-grippers-and-multi-finger-hands)
6. [Tactile and force sensing](#6-tactile-and-force-sensing)
7. [On-robot compute](#7-on-robot-compute)
8. [The category that did not exist: teleoperation hardware](#8-the-category-that-did-not-exist-teleoperation-hardware)
9. [What did not change](#9-what-did-not-change)
10. [How to check an announcement yourself](#10-how-to-check-an-announcement-yourself)

---

## 1. How to read this document

### 1.1 The four maturity labels

Robot hardware announcements are unusually unreliable. A press release, a video
and a product you can order are three different things, and the industry uses the
same vocabulary for all three. Every item in this document therefore carries one
of four labels, and the label is a statement about evidence rather than about
quality.

**Shipping** means you can buy it today. Where the vendor publishes a lead time,
the lead time is given, because a product with a twelve-week lead time and a
product you can have next week are different purchases.

**Announced with a date** means the vendor has committed publicly to a date. An
order page that takes a deposit counts here, not as shipping, because a deposit
is a promise rather than a delivery.

**Demonstrated** means somebody has shown it working, usually in a video, and
there is no way for you to obtain one. Much of the humanoid industry sits here.

**Vapour** means it was announced, no date was given, and nothing has been shown.
This label is not an insult. It is a description of the evidence, and several
respectable companies have products in this state.

### 1.2 Why prices are so hard to quote

Most of the robot arm industry does not publish prices, and the split is not
random. It follows the sales channel.

A vendor that sells through system integrators publishes no price, because the
price depends on the integration. A vendor that sells to individuals runs a web
shop and publishes everything. That single distinction explains almost every gap
in this document.

Of the collaborative arm vendors, none of Universal Robots, Franka Robotics,
Kinova, Doosan Robotics, Techman, Elite Robots, JAKA or Dobot publishes a price
on its own website. Every one of those sites was fetched in September 2026 and
every one routes you to a quote form. The exceptions are UFACTORY, Unitree,
Trossen Robotics and AgileX, all of which run a shop with prices on it, and all
of which appear repeatedly below for exactly that reason.

This produces a bias you should be aware of while reading. The numbers in this
document are concentrated in the parts of the market that sell to individuals,
because that is where numbers exist. It is entirely possible that industrial
arm prices moved and nobody can see it. The honest position is that the
published evidence covers the cheap end well and the industrial end barely at
all.

One more warning about prices from low-cost vendors. A repeatability figure of
0.1 mm on a two-thousand-dollar arm is the vendor's claim, measured by the vendor,
under conditions the vendor does not state. The same figure on a Universal Robots
datasheet is backed by a test standard. Treat the numbers below as what the
vendor published, which is what they are, and not as independently measured.

## 2. Collaborative and industrial arms

A collaborative arm, usually shortened to cobot, is an arm designed to work
beside people without a safety cage, by limiting its own speed and force. This is
the category that Universal Robots created and that everybody else entered.

### 2.1 What a mid-range arm cost in 2024, and what it costs now

This is the headline question, so it goes first, and the answer is not the one
the folklore gives.

Before, in mid-2024, the cheapest capable six-axis arm with a published price was
the UFACTORY xArm 6: 5 kg payload, 700 mm reach, 0.1 mm repeatability. The
Internet Archive's snapshot of [UFACTORY's own product page taken on 24 June
2024](https://web.archive.org/web/20240624075152/https://www.ufactory.cc/product-page/ufactory-xarm-6/)
gives the price as US$8,399.00 to US$8,594.00.

What changed is that nothing changed. [The same page fetched on 23 September
2026](https://www.ufactory.cc/product-page/ufactory-xarm-6/) gives exactly the
same price, US$8,399.00 to US$8,594.00, for exactly the same specification. A
snapshot from January 2025 gives the same figure again. Three readings spanning
twenty-seven months, and the number did not move once.

How that came about is the ordinary economics of a mature product. The xArm 6 is
a harmonic-drive arm built in volume against a stable bill of materials, and
there was no competitive event in that band that forced a cut. The Chinese
entrants that did arrive attacked a different band, which is section 3.

Why it matters is that "arms got cheaper" is folklore when applied to this part
of the market. If you were quoted a mid-range industrial arm in 2024 and waited
for the price to fall, you waited for nothing.

What this comparison still cannot tell you is what happened to the arms nobody
publishes a price for, which is most of the industrial market. A UR10e or a
Franka Research 3 may well have moved. There is no published evidence either way,
and a reseller's figure is not evidence.

The full set of UFACTORY prices, read from the shop's own product feed on 23
September 2026, is worth having because it is one of the few complete published
price lists in the industry. Read it as: the model, what it lifts, and what
UFACTORY charges for it.

| Product | Payload | Published price |
| --- | --- | --- |
| [UFACTORY Lite 6](https://www.ufactory.cc/lite-6-collaborative-robot/) | 600 g | $2,999 |
| [UFACTORY xArm 5](https://www.ufactory.cc/xarm-collaborative-robot/) | 3 kg | $5,299 |
| [UFACTORY xArm 6](https://www.ufactory.cc/product-page/ufactory-xarm-6/) | 5 kg | $8,399 |
| [UFACTORY xArm 7](https://www.ufactory.cc/xarm-collaborative-robot/) | 3.5 kg | $9,999 |
| [UFACTORY 850](https://www.ufactory.cc/ufactory-850/) | 5 kg | $8,999 |

Two entries in the same feed are not arms and are more surprising than the arms
are. UFACTORY publishes $3,000 for a six-axis force-torque sensor and $1,999 for
its xArm Gripper G2. Section 6 comes back to the first of those, because a
published three-thousand-dollar force-torque sensor is a genuine change.

Status: Shipping.

### 2.2 Universal Robots announced a new platform on 14 September 2026

Before, Universal Robots sold the e-Series, launched in 2018, extended upwards
with the UR20 and UR30 and then with the UR15. The UR18 was added on 6 October
2025, according to [Universal Robots' own news
centre](https://www.universal-robots.com/about-universal-robots/news-centre/).
Every one of those is the same architecture with a different arm on the end.

What changed is that on 14 September 2026 — nine days before this document was
written — the same news centre announced "Universal Robots unveils Gen 7, a new
platform for industrial automation and physical AI deployment", described as
"out-of-the-box AI-ready". The arms in it are branded the g-Series, and
[Universal Robots' g-Series page](https://www.universal-robots.com/products/g-series/)
calls it the company's "7th generation robot family within the Gen 7 platform"
and lists three models: the UR10g-1750 at 8 kg payload and 1750 mm reach, the
UR17g-1300 at 15 kg and 1300 mm, and the UR18g-950 at 18 kg and 950 mm.

How it was achieved is stated plainly on that page, and the interesting part is
not the arms. The g-Series brings "power, data, and safety connectivity directly
to the tool flange", with integrated tool flange inputs and outputs at 24 or 48
volts, 5 A peak and 3 A continuous, and 1 gigabit Ethernet "for cameras and
sensors". Universal Robots has moved the wiring for a camera and a smart gripper
inside the arm. That is a response to the fact that almost every modern cell
bolts a camera to the wrist and then runs a cable down the outside of the robot.

Why it matters is that the cable you no longer have to route is one of the
larger hidden costs of integrating an arm, and one gigabit at the flange is
enough for a wrist camera without a separate umbilical.

What it still cannot do is be priced. Universal Robots publishes no price for any
of it. Nor could this document verify a shipping date: the news centre index page
carries the headline and the date, but the individual press release could not be
fetched, because the site serves its article pages from a client-side
application that returns nothing to an automated request.

Status: Announced with a date, for the announcement itself on 14 September 2026.
Whether the g-Series arms are shipping could not be confirmed from a page that
resolves.

A second Universal Robots item belongs here because it is compute rather than
mechanics. [The UR AI
Accelerator](https://www.universal-robots.com/products/ai-accelerator/) is a
bundle of an "Embedded NVIDIA Jetson Orin AGX 64GB compute box" with an Orbbec
Gemini 335Lg depth camera, built on PolyScope X with "full ROS2.0 support", and
the page says it "is now available for order". No price. The reason it matters is
covered in [section 7](#7-on-robot-compute): an arm vendor shipping a named
Jetson module as a catalogue item is a change in what an arm is expected to come
with.

There is also a software-side event with hardware consequences. The same news
centre records, on 16 March 2026, "Universal Robots and Scale AI launch imitation
learning system", unveiling the UR AI Trainer at GTC 2026 and describing data
generated in training cells. A training cell is hardware. Section 8 returns to
this.

### 2.3 Franka is now part of Agile Robots

Before, Franka Emika sold the Panda and then the FR3, and was the default
research arm for anybody who wanted torque sensing in every joint at a price a
university could reach.

What changed is ownership. [Franka Robotics' own site](https://franka.de/) states
that the company was "Founded in 2016, it is part of Agile Robots since 2023".
The product page now lists the Franka Research 3 alongside the "Diana 7 by Agile
Robots", so the two catalogues have merged. It also lists a set of prototypes:
FR3 Duo, Mobile FR3 Duo, a Tactile Mobile Robot, and Franka GELLO and GELLO Duo.

How it happened is a matter of public record only in outline, and this document
does not have a verified account of the insolvency and sale, so it does not give
one. What the vendor's own page states is the sentence quoted above, and that is
what is reported here.

Why it matters is practical. If you are reading a paper from 2022 or 2023 that
used a Franka Panda, the company that made it no longer exists under that name,
and the arm in the paper is two generations back. If you are buying, you are
buying from Agile Robots.

What it still cannot do is tell you a price. Franka publishes none, and the "Buy
now" control is a quote request.

The GELLO prototypes deserve a note of their own. GELLO is an open-source leader
arm for teleoperating a robot arm by hand, and a major arm vendor now lists its
own version as a product. That is section 8.

Status: Franka Research 3, Shipping. FR3 Duo, Mobile FR3 Duo, Tactile Mobile
Robot, Franka GELLO and GELLO Duo are labelled prototypes by the vendor, which
places them at Demonstrated.

### 2.4 The Chinese entrants, and what can actually be checked

The claim you will meet everywhere is that Chinese manufacturers reset the price
floor for collaborative arms. This document can confirm part of that claim and
not the rest, and the distinction matters.

What can be confirmed is that Chinese vendors now dominate the bands below
$10,000 with published prices. UFACTORY, Unitree, AgileX, Dobot and Elephant
Robotics all publish, and their arms are all Chinese-built. Section 3 has the
numbers, and they are genuinely low.

What cannot be confirmed is that they pushed down the price of a UR10e or a
Franka. JAKA, Dobot, Elite Robots and Techman were all fetched in September 2026
and none of them publishes a price for anything. There is no published series a
reader can inspect, so a statement that Chinese competition halved industrial
cobot prices would be folklore repeated with confidence. It may be true. It is
not checkable from vendor sources.

There is, however, one piece of indirect evidence that the pressure is real, and
it is a court docket rather than a price list. Teradyne, which owns Universal
Robots, brought a copyright action against Elite Robots Deutschland in February
2026, and [the Regional Court of Hamburg issued a preliminary injunction in
Teradyne's
favour](https://www.therobotreport.com/german-court-rules-in-favor-of-teradyne-robotics-issues-injunction-against-elite-robots/)
on 21 April 2026, barring Elite Robots Germany from offering the software at
issue and requiring it to disclose which customers had been supplied. In August
2026 Teradyne [sued JAKA Robotics
GmbH](https://www.therobotreport.com/teradyne-robotics-sues-jaka-over-3-universal-robots-patents/)
at the Unified Patent Court in Copenhagen, case UPC-CFI-0003057/2026, over three
Universal Robots patents covering touchscreen robot programming, joint safety
brakes and joint construction. Neither case has reached a final ruling.

How to read that is a matter of judgement rather than fact, and this document
will state its judgement plainly and mark it as such. An incumbent that competes
on price cuts prices. An incumbent that goes to court is defending a position
that price alone is no longer holding. That is the clearest available signal
that the Chinese entrants have become genuinely competitive, and it is a signal
rather than a measurement.

Two other Teradyne numbers are worth recording because they contradict the
common story that the cobot market is collapsing. [Teradyne's own second-quarter
2026
results](https://investors.teradyne.com/news-events/press-releases/detail/445/teradyne-reports-second-quarter-2026-results)
report $100 million in robotics revenue, its first hundred-million-dollar
quarter, up 33 per cent year on year and the fifth consecutive quarter of growth.
Robotics is nonetheless down to 8 per cent of Teradyne's total revenue from 12
per cent a year earlier, because the rest of the company grew faster. The
robotics business is growing; it is simply growing inside a company whose
semiconductor test business is growing faster.

One correction while this subject is open, because it is repeated constantly and
it is wrong. Teradyne Robotics is Universal Robots, Mobile Industrial Robots and
Energid. **Robotiq is not part of it, and neither is OnRobot.** No acquisition of
Robotiq appears anywhere in the public record, and Robotiq's own about page says
nothing about ownership either way.

## 3. Research and low-cost arms

This is where the money actually moved, and it moved in a specific direction:
not the cheapest arms getting cheaper, but the gap between $200 and $8,000
filling up with things that did not exist.

### 3.1 The hundred-dollar arm stopped getting cheaper

Before, in early 2024, the cheapest credible learning arm was the Koch v1.1, a
printed five-axis arm built around Dynamixel XL330 servos.
[Its repository](https://github.com/jess-moss/koch-v1-1) puts the leader arm's
bill of materials at $199 in the United States. The repository is Apache-2.0 and
has had no commits since September 2024.

What changed first was the SO-100, which replaced Dynamixel servos with cheaper
Feetech ones. [The SO-ARM100 repository's README as it stood on 25 October
2024](https://github.com/TheRobotStudio/SO-ARM100/blob/5e0b789aa1a8ac50c53cfeb1967c830528dcae5a/README.md)
gives $241 for a leader and follower pair in the United States and 244€ in
Europe, and $127 for a single follower arm, 128€ in Europe.

What changed since is almost nothing. [The same repository
today](https://github.com/TheRobotStudio/SO-ARM100) gives $229.88 for the pair
and €226.3 in Europe, and $121.94 for a single follower arm, €124.3 in Europe.
That is a fall of about five per cent over twenty-three months. The SO-101
superseded the SO-100 — the README calls the SO-100 documentation deprecated —
but the change was mechanical, chiefly the leader arm's gearing, not a price cut.
As of September 2026 the SO-101 is still the current version in the official
repository, and there is no SO-102 in it.

How the original drop was achieved is worth stating because it explains why it
did not repeat. The Koch used Dynamixel XL330 servos at $24 each. The SO-100 used
Feetech STS3215 servos, which [WowRobo sells
today](https://shop.wowrobo.com/products/so-arm101-diy-kit-assembled-version-1)
at $15.99 each, or $13.99 each in packs of ten. Six servos is most of the cost of
a printed arm, so switching servo supplier was the whole saving. There is no
second saving of that kind available, because the remaining cost is the servos
themselves.

Why it matters is that the hundred-dollar arm is a floor rather than a trend. If
you are waiting for a fifty-dollar arm, the bill of materials says it is not
coming from this direction.

What it still cannot do is a great deal. These arms have no joint torque sensing,
no meaningful payload, and repeatability nobody publishes. They exist to collect
demonstrations and run small policies, which is exactly what
[the learning path](../10_one-arm-training/04_learning-path.md) uses them for.

Status: Shipping. The repository licence is Apache-2.0, which is a software
licence applied to a hardware project — see [section 3.5](#35-open-source-torque-control-arrived-openarm)
for why that distinction is worth checking every time.

### 3.2 The real change was the kit ecosystem

Before, building an SO-100 in 2024 meant owning a 3D printer, sourcing servos
from Alibaba, and assembling the arm yourself. The bill of materials was the
product. That is a large barrier disguised as a low price, and it is the reason
the hundred-dollar arm was less accessible than its headline suggested.

What changed is that resellers appeared. The SO-ARM100 repository now lists ten
of them, in Switzerland, the United States, China, Japan, South Korea and the
European Union, selling printed frame kits, electronics kits, complete kits and
assembled arms. [WowRobo](https://shop.wowrobo.com/products/so-arm101-diy-kit-assembled-version-1)
publishes $199 for the do-it-yourself kit, $259 and $299 for assembled versions.
Seeed Studio lists [an SO-ARM100 servo motor kit at
$200](https://www.seeedstudio.com/SO-ARM100-Low-Cost-AI-Arm-Kit.html), $196 each
in tens, without printed parts, and showed as out of stock when fetched.

How it happened is straightforward commerce. An open design with a large user
base and no trademark restriction is an invitation to manufacture, and the
Apache-2.0 licence permits exactly that. The design's authors get no royalty and
the buyer gets an assembled arm.

Why it matters is that the effective cost of entry went up and the effort went
down, and the second matters more. An assembled SO-101 at $299 against a $122
bill of materials is a $177 premium for not owning a printer and not spending a
weekend. For most people that is the transaction that made the arm real.

What it still cannot do is guarantee anything. These are third-party
manufacturers of somebody else's open design. There is no warranty position, no
support commitment, and no guarantee that two sellers' arms are dimensionally
identical, which matters when a trained policy is supposed to transfer between
robots.

Status: Shipping, from multiple vendors, with stock varying.

### 3.3 The two-thousand-dollar arm filled the gap

Before, the choice was a printed arm at a few hundred dollars with no payload, or
an industrial arm at $8,000 and up. There was very little between them, and the
gap was the single most awkward fact about equipping a manipulation lab.

What changed is that [AgileX's PiPER](https://global.agilex.ai/products/piper)
sits in it at $1,999: six degrees of freedom, 1.5 kg payload, 626 mm reach, an
arm weighing 4.2 kg, and a stated repeatability of 0.1 mm. AgileX's own store
publishes the price and states Python, ROS 1 and ROS 2 support. A PiPER-X variant
is listed at the same $1,999.

How it was achieved is the same answer as everywhere in this section: an
integrated actuator module built in volume for the Chinese domestic market, sold
through a Shopify storefront that skips the integrator channel entirely.

Why it matters is that 1.5 kg of payload with a real serial interface is enough
to do actual manipulation work — it will hold a drill, a bottle or a tool — at a
price a single researcher can approve. The band between a toy and an industrial
robot stopped being empty.

What it still cannot do is prove its own numbers. The 0.1 mm repeatability figure
is stated without a test standard or measurement condition, and this document
found no independent measurement of it. Treat it as a claim.

Status: Shipping.

### 3.4 Trossen replaced the ALOHA kit, and it did get cheaper

This is the clearest like-for-like price fall in the document, because one vendor
published both numbers.

Before, the standard bimanual imitation-learning rig was Trossen's ALOHA
Stationary kit: two ViperX 300 S arms as followers and two WidowX 250 S arms as
leaders. [The Internet Archive's snapshot of 2 April
2024](https://web.archive.org/web/20240402231620/https://www.trossenrobotics.com/aloha-stationary)
prices it at $29,999.95, and a snapshot from March 2025 gives the same figure.
The follower arm was the expensive part: [a snapshot of the ViperX 300 page from
18 February
2025](https://web.archive.org/web/20250218090812/https://www.trossenrobotics.com/viperx-300)
gives $6,129.95 for 6 degrees of freedom, 750 mm reach and a 750 g payload.

What changed is that Trossen retired the line and replaced it. The ALOHA kits
page now says "ALOHA IS NOW TROSSEN AI". [Trossen's Stationary
AI](https://www.trossenrobotics.com/stationary-ai) is $23,995.95 and contains
"2X Leader-Follower WidowX AI Arm Pairs", with an average production time of two
to three weeks. [The WidowX AI arm](https://www.trossenrobotics.com/widowx-ai)
sells on its own at $4,545.95 for the base version, $4,685.95 as a leader and
$4,995.95 as a follower, with 6 degrees of freedom, 1.5 kg payload, 700 mm reach
and 1 mm repeatability.

So the kit fell from $29,999.95 to $23,995.95, a drop of twenty per cent, and the
per-arm payload doubled from 750 g to 1.5 kg at the same time. The single arm
fell from $6,129.95 to $4,545.95, a drop of twenty-six per cent, for twice the
payload. That is the "arms got cheaper" story actually being true, with the
vendor's own published numbers on both ends.

How it was achieved is visible in the product change. Trossen stopped selling two
different arms and started selling one. The old kit paired a large follower with
a small leader; the new one uses identical WidowX AI arms in both roles, with
only the end fitting differing. Building one arm instead of two, in higher
volume, is the ordinary way a manufacturer takes cost out.

Why it matters is that this is the rig most published bimanual imitation-learning
work runs on, so its price is the entry fee to reproducing that work. Six
thousand dollars came off that fee, and the resulting arms lift twice as much.

What it still cannot do is compete on precision. One millimetre of repeatability
is ten times worse than the industrial arms in section 2, and it is the number
that decides whether a learned policy can be replayed reliably. It also still has
no joint torque sensing, so contact-rich work needs a separate wrist sensor.

Status: Shipping, average production time two to three weeks, published by the
vendor.

One more thing on that page is worth reading as a hardware fact about learning.
Trossen sells an optional workstation with the kit — an NVIDIA RTX 5090 and an
Intel Core Ultra 9 — at $10,995.95. The training computer now costs half as much
as the robot.

### 3.5 Open-source torque control arrived: OpenArm

This is the most significant new open hardware in the period, and it is the one
with the licence trap in it.

Before, an arm you could back-drive by hand and command in torque rather than
position meant a Franka or a Kinova, from a vendor that publishes no price, on a
procurement timescale measured in months. Torque control is what
[stiffness and force control](../08_arm-movement/04_controlling-the-move.md#4-position-stiffness-and-force)
needs underneath it, so this
was a hard floor on who could do contact-rich work.

What changed is [OpenArm](https://docs.openarm.dev/), from Enactic. The
documentation gives 7 degrees of freedom per arm, a nominal payload of "4.1 kg
(held for 1 minute in the worst posture)" and a peak payload of "6.0 kg (3 s move
+ 1 s hold in the worst posture)", quasi-direct-drive backdrivable joints, a
CAN-FD control bus, an aluminium and stainless steel structure, and a compact
parallel gripper with an in-hand camera. Note how the payload figures are
qualified: the vendor states the posture and the duration, which is better
practice than most of the industry manages and is exactly the habit
[the gripper document](../07_gripping/02_grippers-and-hardware.md#1-how-to-read-a-gripper-datasheet)
asks you to look for.

It is also buyable without building it. WowRobo lists the OpenArm V1.1 at $5,400
and OpenArm 2 as a bimanual set at $6,500 and $7,300.

How it was achieved is the quasi-direct-drive actuator. A quasi-direct-drive
joint uses a motor with a very low gear ratio, so the motor's own torque is felt
almost directly at the joint and the joint can be pushed back by hand. Those
actuators became a commodity part, and Enactic maintains [a repository of notes
on the DAMIAO actuators](https://github.com/enactic/damiao) it uses. The arm is a
frame around bought-in actuators, which is why it costs a fifth of what a
comparable closed arm does.

Why it matters is that force control stopped requiring a purchase-order
conversation. A 7-degree-of-freedom backdrivable arm at $5,400 puts impedance
control, human-robot contact and compliant assembly inside a normal project
budget.

What it still cannot do is be treated as permissively licensed, and this is the
trap. The software repositories — `openarm`, `openarm_ros2`, `openarm_can`,
`openarm_description` and the rest — are Apache-2.0. But
[`openarm_hardware`](https://github.com/enactic/openarm_hardware), which holds
the CAD data and the manufacturing information, is **CERN-OHL-S-2.0**. The S
stands for strongly reciprocal: if you make and distribute a product based on
those designs, you must make your own design files available under the same
licence. That is the hardware equivalent of the GPL, and it is a completely
different obligation from the Apache-2.0 on the software in the same
organisation. Reading the GitHub badge on the main repository and concluding the
hardware is Apache-2.0 would be a real and expensive mistake.

Status: Shipping, through a third-party seller.

### 3.6 Whole robots, not just arms

Three more things became buyable that are not arms but are what people actually
put arms on.

[XLeRobot](https://github.com/Vector-Wangel/XLeRobot) is a dual-arm mobile home
robot built on SO-101-derived arms, Apache-2.0, at version 0.3.0 since 30 August
2025, and the repository states a basic configuration cost of about $660, with
$30 for a stereo head camera, $79 for a Raspberry Pi and $220 for a RealSense
depth camera as options. WowRobo sells kits at $239, $349 and $579. The
repository's own honesty about what it costs you is worth quoting: assembly
requires "at least a day" and familiarity with programming.

[Reachy 2](https://www.pollen-robotics.com/reachy-2/) from Pollen Robotics, now
"Part of Hugging Face", has two 7-degree-of-freedom arms with about 3 kg of
payload each, and the software is Apache-2.0. The page describes the hardware as
open but does not name the hardware licence, so this document does not state one.
No price is published on that page.

[Reachy Mini](https://huggingface.co/blog/reachy-mini) is the small desk robot
from the same team, at $399 for the lite version and $499 for the wireless
version with a Raspberry Pi 4 and a battery, with a quoted delivery time of about
ninety days. It has no arms and no gripper, which is worth saying plainly because
it is frequently mentioned in the same breath as the arms and it cannot
manipulate anything.

Status: XLeRobot and Reachy Mini, Shipping. Reachy 2, Shipping, price on
application.

## 4. Humanoid arms and hands

Humanoids are outside this repository's subject, which is arms bolted to tables.
They appear here for one reason: the money that went into them paid for arms and
hands that you can now buy, and those arms and hands work perfectly well on a
table. This section covers only that part, and ignores legs, balance and
locomotion entirely.

### 4.1 What is actually buyable, and at what price

Before, a humanoid was something you saw in a video. The arms inside it were not
sold, no price was published, and the specification sheets did not exist.

What changed is that Unitree and AgiBot both opened storefronts with prices in
United States dollars. Read the following table as: the robot, what one arm can
lift, and what the vendor charges. Every figure is from the vendor's own page,
fetched in September 2026, and a dash means the vendor publishes nothing.

| Robot | Arm degrees of freedom | Arm payload | Published price | Status |
| --- | --- | --- | --- | --- |
| [Unitree R1 AIR](https://www.unitree.com/R1) | 4 | — | $4,900 | Shipping |
| [Unitree R1](https://www.unitree.com/R1) | 5 | — | $5,900 | Shipping |
| [Unitree G1](https://www.unitree.com/g1) | 5 | about 2 kg, about 3 kg on the EDU version | $13,500 | Shipping, backordered |
| [Unitree H2](https://www.unitree.com/H2) | 7 | 7 kg rated, 15 kg peak | $29,900 | Announced; store shows unavailable |
| [Unitree H1](https://www.unitree.com/h1) | 4, expandable | — | $90,000 | Shipping |
| [AgiBot X2 Neo](https://store.agibot.com/) | — | — | $25,600 | Shipping |
| [AgiBot A2 Lite](https://store.agibot.com/) | — | — | $44,560 | Shipping |
| [AgiBot A2 Ultra](https://www.agibot.com/products/A2_Ultra) | 7 | about 2 kg | — | Shipping, price on application |
| [1X NEO](https://www.1x.tech/neo) | 7 | 18 lb, about 8.2 kg | $20,000, or $499 a month | Announced with a date |

Three things in that table matter more than the prices.

**The arm payload is the number to read, and it is small.** A humanoid that
carries 25 kg carries it with both arms and a simple end fitting. Per arm, with a
hand on the end, the figures are 2 kg on a G1, about 2 kg on an AgiBot A2 Ultra,
7 kg rated on a Unitree H2 and 8.2 kg on a 1X NEO. Those are the numbers that
decide what a manipulation task can involve, and they sit in the same range as
the research arms in section 3.

**A cheap humanoid may not be programmable.** Unitree's own store page notes that
the $13,500 G1 "does not support secondary development". Research use requires
the EDU edition, which is quoted rather than priced. Buying the headline price
and then discovering you cannot write code for it is a real failure mode.

**1X NEO is an order page, not a product.** [The order
page](https://www.1x.tech/order) takes a $200 deposit described as "Fully
Refundable" and says "US Deliveries start 2026". A refundable deposit against a
year is the definition of Announced with a date, and this document does not
report it as shipping.

### 4.2 Two arms you can buy without the robot

The genuinely useful development for anyone working on manipulation is that arms
started being sold on their own.

[Unitree's store](https://shop.unitree.com/collections/all) lists the R1-7a, a
seven-axis arm, at $1,650, with a student price of $899 shown but unavailable
when the store was read. The listing was published on 4 September 2026, which
makes it three weeks old at the time of writing. The same store has sold the Z1
arm since 2022 at $15,999.

That contrast is the whole story of this section in two rows of one shop's
catalogue. A seven-axis arm from the same vendor went from $15,999 to $1,650 in
four years. The two are not the same product — the Z1 is a heavier, older,
higher-payload design and Unitree publishes no payload for the R1-7a at all — so
this is not a like-for-like price fall and should not be reported as one. What it
is, is evidence that the humanoid actuator supply chain now produces an arm at a
price the arm industry could not previously reach.

How it was achieved is the actuator again, and the numbers from the humanoid
makers say so directly. Figure's own account of ramping production, [published on
29 April 2026](https://www.figure.ai/news/ramping-figure-03-production), reports
building "9,000+ actuators" across more than ten distinct types in the course of
building its robots. Inspire Robots [announced on 8 September
2026](https://en.inspire-robots.com/news/inspire-robots-celebrates-10000-units-of-the-dexterous-hands/)
that it had delivered 10,000 dexterous hands cumulatively, a five-fold increase
in shipment volume, on an actuator capacity of 100,000 units a year. When a
company builds actuators at that rate for one product, the marginal cost of
putting six of them in a frame and selling it as an arm collapses.

Why it matters is that the cheapest seven-axis arm is now cheaper than the
cheapest six-axis industrial arm by a factor of five.

What it still cannot do is come with a specification. Unitree publishes no
payload, no reach and no repeatability for the R1-7a, only that it has high
precision, bionic joints and open programming interfaces. Buying it is buying an
unspecified arm.

Status: Shipping, for both.

### 4.3 The hands: separately purchasable at last, but not from everyone

Before, a multi-finger hand meant Shadow Robot or Wonik Allegro, neither of which
publishes a price, on a procurement cycle to match.
[The gripper document's section on multi-finger
hands](../07_gripping/02_grippers-and-hardware.md#6-multi-finger-hands) has their
specifications and records that neither publishes a price. That is still true in
September 2026.

What changed is AgiBot. [Its store](https://store.agibot.com/) lists the OmniHand
2025 at $4,420 and the same hand with tactile sensing at $5,360 — so the tactile
option is a $940 line item you can read off a web page.
[The OmniHand O12 product page](https://www.agibot.com/products/OmniHand_O12)
describes it explicitly as "offered as a standalone accessory compatible with
multiple robot platforms" and gives 12 active degrees of freedom out of 19 total,
five fingers, a typical maximum fingertip force of 20 N, a load of 35 kg with the
palm up and 5 kg with the palm down, a weight of 750 g or less, and tactile
sensing comprising three-axis fingertip force and one-axis palm force over "150+
tactile points" at a resolution of 0.01 N.

Unitree's hands are the counter-example and the disappointment. The
[Dex3-1](https://www.unitree.com/Dex3-1) has 7 degrees of freedom across three
fingers, 33 tactile sensors covering 10 g to 2500 g, a maximum held weight of
500 g and a mass of 710 g. The [Dex5-1](https://www.unitree.com/Dex5-1) has 20
degrees of freedom of which 16 are active, five fingers, a fingertip grip force
of 10 N, a load of 3.5 kg with the palm down and 4.5 kg with the palm to the
side, a fingertip accuracy of ±1 mm and a mass of 1100 g. The tactile version,
the Dex5-1P, carries 94 tactile sensors per hand; the base Dex5-1 has none. And
neither appears as a purchasable item anywhere in Unitree's store. They are
configuration options on an EDU humanoid, quoted by email. You cannot buy a
Unitree hand.

Why the AgiBot listing matters is that it is the first time a five-finger hand
with fingertip force sensing has had a public price at all, let alone one under
six thousand dollars. Against a Shadow Dexterous Hand, which the
[gripper document](../07_gripping/02_grippers-and-hardware.md#6-multi-finger-hands)
describes as quote-only, that is a different kind of purchase.

What it still cannot do is lift anything while being dexterous. The pattern is
consistent across every hand in this section: Dex3-1 at 500 g, Dex5-1 at 3.5 kg
palm-down, OmniHand at 5 kg palm-down. The 15 kg and 23 kg payload figures that
appear in humanoid marketing belong to arms with simple grippers on the end, not
to arms with hands on the end. Nobody sells a hand that is both dexterous and
strong, and this is the single most reliable limitation in the whole category.

Two smaller cautions about hand specifications, because they are systematically
misreported. First, actuated degrees of freedom, total degrees of freedom and
joint count are three different numbers, and vendors quote whichever is largest.
Unitree's "20 Degrees of freedom (16 active+4)" and AgiBot's "12 active DoF, 19
total" are both honest because they give the qualifier; a secondary source that
drops the qualifier is not. Second, tactile sensing is frequently an upsell
rather than a feature — the Dex5-1P and the $940 AgiBot option are both separate
products from the hands they resemble.

Status: AgiBot OmniHand, Shipping with a published price. Unitree Dex3-1 and
Dex5-1, Shipping but bundled only, no published price. Shadow and Allegro,
Shipping, quote only.

### 4.4 Which humanoids have actually been built, and in what numbers

This is the part the announcements are worst at, so it is worth separating the
verified numbers from the rest.

Figure publishes the most detail of anyone. [Its production
account](https://www.figure.ai/news/ramping-figure-03-production) of 29 April
2026 reports "over 350 of our third generation humanoid robots" delivered, a rate
that went "from 1 Figure 03 per day to 1 per hour" in under 120 days, more than
9,000 actuators, over 500 battery packs, an end-of-line first-pass yield above 80
per cent and a battery line at 99.3 per cent. [Its earlier announcement of the
BotQ factory](https://www.figure.ai/news/botq) of 15 March 2025 claims capacity
for 12,000 robots a year and a goal of 100,000 over four years.
[Figure 03 itself](https://www.figure.ai/news/introducing-figure-03), announced 9
October 2025, publishes that its fingertip sensors "detect forces as small as 3
grams" and that each hand contains an embedded palm camera. It does not publish
the hand's degrees of freedom, and this document does not state one.

Three hundred and fifty robots is a real number and it is also a pilot fleet.
Against it, Inspire Robots delivered 10,000 hands. The category that reached
volume manufacturing is the hand, not the humanoid.

Several well-known robots publish very little. [Boston Dynamics'
Atlas](https://bostondynamics.com/atlas/) gives 56 total degrees of freedom, a
2.3 m reach, an instantaneous weight capacity of 50 kg and a sustained capacity
of 30 kg, and states that it has "tactile and 360° camera view" — but publishes
no per-arm degrees of freedom, no hand specification, no taxel count and no
price. [Agility's Digit 5](https://agilityrobotics.com/solutions/digit-5) gives
23 kg of payload and 2.2 m of reach and states on the page itself that "Digit 5
is in development and the features, specifications, capabilities, and designs
shown are subject to change". [Apptronik's Apollo
2](https://apptronik.com/apollo/apollo-2) publishes no numbers at all — no
payload, no degrees of freedom, no price, no date.

Three vendors could not be checked and this document quotes nothing for them.
Tesla's Optimus page returns HTTP 403 to any automated request, so the widely
repeated 22-degree-of-freedom hand figure for Optimus Gen 3 is not verified here.
Be careful with that number in particular, because 1X publishes 22 degrees of
freedom per hand for NEO, and the two claims are easy to confuse. Fourier's site
is a client-side application that serves no content to a fetch, and its
alternative domain fails its TLS handshake. RobotEra's site, which would carry
the XHand specification, is client-rendered in the same way. Those three products
exist; their numbers are not reported here because none could be obtained from a
source that resolves.

Status: Figure 03, Shipping to Figure's own customers and not for sale. Atlas,
Demonstrated, with Boston Dynamics describing early field testing at Hyundai and
publishing no dates or unit counts. Digit 5, Announced. Apollo 2, Demonstrated.
Optimus, Fourier and RobotEra, unverified.

## 5. Grippers and multi-finger hands

[Grippers and the hardware around
them](../07_gripping/02_grippers-and-hardware.md) is the catalogue, and it is
current to September 2026. This section records only what moved.

### 5.1 Robotiq now maintains its own ROS 2 driver

Before, the most widely used driver for the most widely used collaborative
gripper was a community project. The gripper document records the position
exactly: the README of `PickNikRobotics/ros2_robotiq_gripper` says "this is not
sponsored or maintained by Robotiq", and its released-package table covered
Humble, Iron and Rolling but not Jazzy, which is the long-term release most cells
run on.

What changed is that on 26 August 2026 [Robotiq released official ROS 2
packages](https://blog.robotiq.com/robotiq-releases-ros-2-packages-for-adaptive-grippers).
They live at [github.com/robotiq/ros](https://github.com/robotiq/ros) under the
BSD-3-Clause licence, build Humble, Jazzy and Lyrical from a single branch with
Rolling on non-blocking continuous integration, and run the gripper at 200 Hz.
Robotiq describes them as a drop-in successor to the community driver. The
repository was last pushed on 23 September 2026, the day this document was
written.

How it came about is the ordinary consequence of a product becoming
infrastructure. A vendor tolerates a community driver until enough customers
depend on it, and then the support burden of not owning it exceeds the cost of
owning it.

Why it matters is that the Jazzy gap is closed, and it closes the specific
warning in
[the gripper document's driver table](../07_gripping/02_grippers-and-hardware.md#9-drivers-ros-2-packages-and-licences).
If you deferred a Robotiq gripper because its driver did not target your
distribution, that reason has expired.

What it still cannot do is change the licence position elsewhere. Schunk's ROS 2
drivers remain GPL-3.0 and GelSight's software development kit remains GPL-3.0,
and both of those are still the live licensing traps in that table.

Status: Shipping.

The driver is one of three pieces. Robotiq groups them under the name
[Contact Core](https://robotiq.com/contact-core-robotiq), its software layer for
what it calls physical artificial intelligence: the ROS 2 package, a standalone
C++ software development kit, and a set of Isaac Sim simulation assets. The
assets were published on 22 September 2026, one day before this document was
written, with variants for both the PhysX and the Newton physics backends.
Newton is built on MuJoCo-Warp and, according to Robotiq, "models a closed loop
natively, as an equality constraint rather than as a tree plus a patch", which is
the thing that makes an underactuated gripper hard to simulate correctly. A
gripper vendor maintaining its own simulation models is new behaviour, and it is
the useful kind, because
[the gripper document's note on `mujoco_menagerie`](../07_gripping/02_grippers-and-hardware.md#9-drivers-ros-2-packages-and-licences)
describes how awkward third-party gripper models are to license correctly.

The assets repository is the one to read carefully.
[github.com/robotiq/isaacsim_assets](https://github.com/robotiq/isaacsim_assets)
is BSD-3-Clause with a carve-out: parts of the PhysX 2F-85 asset were adapted
from NVIDIA's Isaac Sim and SimReady libraries and remain under CC BY 4.0, with
separate licence files shipped beside the affected files. GitHub's own licence
detection reports the repository as unclassified for exactly that reason. A
mixed-licence repository is not unusual and it is not a problem, but it is not
what a one-word badge would tell you.

Robotiq says the next step, embedded intelligence in the fingertip itself, is due
in the fourth quarter of 2026. That is Announced with a date.

One adjacent event from the same day belongs here because it affects the software
underneath every arm in this repository. On 23 September 2026 [Qualcomm announced
that it will acquire PickNik
Robotics](https://www.qualcomm.com/news/releases/2026/09/qualcomm-to-acquire-picknik-to-advance-the-future-of-open-roboti),
the maintainers of MoveIt, and stated that MoveIt will remain open source.
PickNik also wrote the community Robotiq driver that Robotiq has now replaced.
[MoveIt 2 is the motion planning framework this repository
uses](../09_tools-and-libraries.md#5-moveit-2-planning-a-safe-path), so its
ownership is worth knowing about. The acquisition is Announced; nothing has
completed.

### 5.2 Tactile fingertips became a gripper accessory

Before, adding touch sensing to a production gripper meant a research sensor, a
mount you designed yourself and a driver you integrated yourself. The gripper
document's [section on gripper
sensors](../07_gripping/02_grippers-and-hardware.md#8-the-sensors-that-go-on-a-gripper)
describes that world: GelSight Mini as a camera behind a consumable gel,
Contactile's PapillArray as a research instrument, and nothing that a factory
would buy as a spare part.

What changed is [Robotiq's TSF-85 tactile sensor
fingertips](https://robotiq.com/tactile-sensor-fingertips), launched in January
2026. They replace the
standard fingertips on the 2F-85 and 2F-140 grippers. Each one carries 28 taxels
— individual pressure-sensing elements — in a four-by-seven grid, samples at 1000
Hz, covers a force range of 0 to 225 N, includes a three-axis inertial
measurement unit for vibration, measures 28.4 mm by 44 mm, and is stated as
"Tested to over 2 million cycles".

How it was achieved is packaging rather than physics. A taxel array at this
resolution is not new; putting it in the exact shape of an existing fingertip, on
a sensor rated for two million cycles, is the part that took a manufacturer.

Why it matters is the cycle rating. The GelSight Mini gel is rated for 1,000 coin
presses and is a consumable; two million cycles is the same order as the gripper's
own service interval, which means a tactile fingertip can now live in a production
cell rather than on a bench.

What it still cannot do is be priced. Robotiq publishes no price and the page
offers a quote request, so this is not a part you can budget for from public
information.

Status: Shipping, price on application.

### 5.3 Multi-finger hands became genuinely affordable

Before, a research hand cost what Shadow or Wonik Allegro quoted, and neither
publishes a number. The practical floor for anything with five independently
controlled fingers was tens of thousands.

What changed is a spread of options across three orders of magnitude, all of them
with published prices, all of them reachable in September 2026. Read the table as:
the hand, how many degrees of freedom the maker claims and of what kind, what it
costs, and who publishes that cost.

| Hand | Degrees of freedom | Published price | Status |
| --- | --- | --- | --- |
| [AmazingHand](https://github.com/pollen-robotics/AmazingHand), from Pollen Robotics | not published | under €200 in parts; $99 unassembled, $139 assembled from a reseller | Shipping |
| [LEAP Hand v2](https://v2.leaphand.com/) | "16 DOF with 8 powered motors", four fingers | headline "$200"; the project's own parts page totals $559.48 | Shipping as a self-build |
| [RUKA Hand](https://shop.wowrobo.com/products/ruka-hand-open-source-robotic-hand-by-nyu), from New York University | not published | $549 as a kit, $799 assembled | Shipping |
| [Seed Robotics RH4D](https://www.seedrobotics.com/ordering) | 11, from 4 actuators | from €1,199 plus tax | Shipping |
| [Seed Robotics RH6D](https://www.seedrobotics.com/ordering) | 15, from 6 actuators | from €2,899 plus tax | Shipping |
| [AgiBot OmniHand 2025](https://store.agibot.com/) | 12 active of 19 total, five fingers | $4,420, or $5,360 with tactile sensing | Shipping |
| [Seed Robotics RH8D](https://www.seedrobotics.com/ordering) | 19, from 8 actuators, five fingers, spherical wrist | from €5,599 plus tax | Shipping |
| [PaXini DexH13](https://mall.paxini.com/product/dex/66f27ea530cd11a8e9d1d5ff) | 16, of which 13 active, four fingers | ¥98,000 for a left and right pair | Shipping |
| [Inspire RH56 series](https://inspire-robots.store/collections/the-dexterous-hands) | 6, across 12 joints | $20,599.99 to $25,399.99 | Shipping, see the caution below |
| [Wonik Allegro](https://www.allegrohand.com/) | 9 on the V5, 16 on the V5 Plus, 20 on the V6 F | none published | Shipping, quote only |
| [Shadow Dexterous Hand](https://shadowrobot.com/) | 20 actuated across 24 joints | none published | Shipping, quote only |

How it was achieved differs at each end of that table and the difference decides
what you get. The three cheapest are printed frames around hobby servos, with the
design given away and the assembly given to you. The AgiBot and Seed Robotics
hands are industrially manufactured products riding on the actuator volumes
described in [section 4.2](#42-two-arms-you-can-buy-without-the-robot). The two
at the bottom are low-volume instruments with tendon drives and sensor counts the
cheap hands do not attempt.

Why it matters is that the entry price for dexterous manipulation research fell
from a procurement exercise to a purchase order, and in the AmazingHand's case to
less than the cost of the arm it bolts onto. The cheapest five-finger hand with a
price its own maker publishes is now the AgiBot OmniHand at $4,420, with Seed
Robotics' RH8D at €5,599 the cheapest from a European vendor.

What they still cannot do is hold anything. None of the cheap hands publishes a
payload, and the ones that do publish are small: an AgiBot OmniHand manages 5 kg
palm-down and a Unitree Dex3-1 manages 500 g. A cheap five-finger hand is a
research instrument for studying grasp and in-hand motion, not a way to pick
things up. If picking things up is the job,
[a two-finger gripper is still the right answer](../07_gripping/02_grippers-and-hardware.md#2-two-finger-parallel-and-adaptive-grippers)
and it is not close.

Four things in that table are widely misreported and are worth stating plainly.

**Inspire is not the budget option.** It is frequently described as the cheap
Chinese hand, and the only Inspire prices that can actually be read run from
$20,599.99 to $25,399.99. Those come from an export storefront whose vendor field
names Beijing Inspire Robots and whose returns address is an inspire-robots.com
one, but Inspire's own corporate site does not link to that store and publishes
no prices at all. Treat the figures as the best available and not as
vendor-confirmed.

**LEAP Hand v2's "$200" is not the cost of the hand.** The project's own parts
page totals $559.48, of which $249.95 is servos and $309.53 is everything else,
including $73.67 of fasteners. The $200 figure is roughly the motor and driver
share. A LEAP Hand v2 Advanced at 21 degrees of freedom is quoted at $3,000 with
its files to be released on paper acceptance, which is Announced rather than
shipping.

**The Allegro Hand V5 is a three-finger hand.** Wonik's own specification is
three fingers of three joints each, giving nine degrees of freedom, at 1,050 g —
not the four-finger sixteen-degree-of-freedom device most descriptions assume,
which is the V5 Plus. Wonik launched the **Allegro Hand V6 F** on 7 September
2026 with five fingers, 20 active degrees of freedom and a mass of 1,150 g, and
still publishes no price.

**Unitree's Dex5-S is press reporting, not a product listing.** A 22-degree-of-
freedom hand at ¥39,900 was reported on 22 September 2026. Unitree's own product
page for it returns HTTP 404 and no Dex hand of any kind appears in the shop's
product feed. Do not treat ¥39,900 as a vendor price. Status: Announced.

Three licence cautions in that table, because hardware licences are misdescribed
more often than they are read.

**AmazingHand's repository is Apache-2.0**, read from
[the repository itself](https://github.com/pollen-robotics/AmazingHand) in
September 2026. That is a software licence applied to a hardware project, which
is common and legally awkward, because Apache-2.0 talks about source code and
object code and says nothing about design files. It is permissive in intent and
you should read it as such, but it is not a hardware licence.

**RUKA's repository is MIT**, from
[the project's code](https://github.com/ruka-hand/RUKA), with the same caveat.

**LEAP Hand v2's CAD is not simply downloadable.** The site offers a CAD request
form rather than a file, and states no licence on the page. Its predecessor's
driver, as
[the gripper document records](../07_gripping/02_grippers-and-hardware.md#9-drivers-ros-2-packages-and-licences),
is CC BY-NC 4.0, which forbids commercial use. A $200 hand you cannot use in a
product is still a $200 hand, but you should know which one you have bought.

### 5.4 The 64-fold downcost nobody noticed: Pinc'Open

Before, Reachy 2's gripper was the "Pincette": machined metal driven by a
Dynamixel XM430-W210 servo. Pollen Robotics states its own bill of materials at
about €1,700 per unit at low volume.

What changed is that Pollen open-sourced a reimplementation.
[Pinc'Open](https://github.com/pollen-robotics/PincOpen) replaces the machined
metal with printed parts and the Dynamixel with a Feetech STS3215, and is
designed to bolt onto an SO-ARM100 or SO-101. Its own bill of materials is
€26.46: €14.49 for the servo, €6.29 for the servo driver board, and €2.83 for all
eleven printed parts together. On an SO-101 the marginal cost is about €12,
because the arm already has a servo at that joint.

How it was achieved is the same substitution that produced the cheap arms in
section 3, applied to the end effector: a €14 serial-bus servo in place of a
€100-class Dynamixel, and printed plastic in place of machined aluminium.

Why it matters is the ratio. The same function, from the same company, went from
about €1,700 to about €26 — a factor of about sixty-four — with the loss in
precision and durability being exactly what you would expect and exactly what the
application can usually absorb.

What it still cannot do is be combined carelessly. **Pinc'Open is licensed
CC BY-SA 4.0**, read from the repository's own licence file. That is a copyleft
licence: derivatives of those parts must be released under the same terms. The
SO-101 it bolts onto is Apache-2.0. Bolting the two together produces an assembly
under two different hardware licences with different obligations, and several
downstream projects describe the whole stack as Apache-2.0, which is wrong about
the gripper.

Status: Shipping, as files.

### 5.5 New gripper technology, and what is only a paper

Four things shipped in the period that are not simply cheaper versions of
existing products.

Schmalz launched the **FSGA-78 CF bellows suction cup** on 15 May 2026, with a
very soft silicone sealing lip that Schmalz describes as working by a "clingfish
effect", conforming to rough-sawn timber and textured surfaces that defeat an
ordinary cup. That attacks the exact failure mode
[the gripper document names as suction's first
limitation](../07_gripping/02_grippers-and-hardware.md#3-suction). No price is
published.

Schmalz also launched **mGrip Basic** with an SRCU Basic control module on 2 June
2026, a cheaper tier of the line it acquired from Soft Robotics: up to 10 kg, a
workpiece width up to 300 mm, 120 picks per minute, IP69K, with a 24 V control
module running on 3.0 to 6.0 bar. Schmalz says it "lowers the entry hurdle" and
publishes no price. Status: Shipping.

**Toyota released YUBI** on 11 May 2026, a teleoperation glove with a matching
gripper and mounting flanges for Franka, OpenArm and the Unitree G1. It is worth
naming here for its licensing as much as its function: the hardware repository
[Toyota/yubi-hw](https://github.com/Toyota/yubi-hw) is **CERN-OHL-W-2.0**, the
weakly reciprocal variant, while the software sits in a different GitHub
organisation under Apache-2.0. Its bill of materials contains thirty-nine lines
and no prices at all, and several parts are specified as machined aluminium, so
the real cost needs quotes. Status: Shipping, as files.

Two things are frequently described as arriving and have not.

**Electroadhesion — holding an object by electrostatic attraction rather than
friction or vacuum — is research, not product.** Two recent papers exist, a
review in npj Robotics on 3 September 2025 and
[a paper on electroadhesive clutches on 30 March
2026](https://www.nature.com/articles/s44182-026-00084-1). The company that
commercialised the idea, Grabit, still has a live website whose most recent news
item is dated 19 June 2018. Status: Demonstrated.

**Gecko-adhesion grippers were announced and their shipping status is not
stated.** geCKo Materials showed four products on 29 October 2025, including a
gripper for smooth surfaces such as solar panels and glass and a semiconductor
wafer-handling tool demonstrated at 5.4 g of repeated acceleration on a FANUC
arm. No prices were given and the announcement does not say the products ship.
Status: Announced. OnRobot's own Gecko Gripper, by contrast, is still in its
catalogue and has been for years.

### 5.6 Two things that are repeated and are wrong

**The Fin Ray patent has not been shown to have expired.** The compliant finger
that bends towards a contact, used by every soft two-finger gripper, is usually
said to be freely copyable now. This document could not verify that. Every patent
database refused an automated request — Google Patents returned 503, Espacenet
and the European Patent Office register returned 403, and the World Intellectual
Property Organization returned 404. The best candidate for the founding patent,
EP1203640A2 by Leif Kniese with a priority date of 1 November 2000, shows no
recorded grant in the one index that answered. A separate Festo patent,
EP2735408B1, was filed on 27 November 2012 and granted on 20 April 2016, which by
the twenty-year rule runs to 2032 at the outside — that is arithmetic from a
verified filing date, not a reading of legal status. Separately, "Fin Ray
Effect®" is used as a registered trademark, and a trademark does not expire on a
patent's schedule, which is why the open projects all say "fin-ray-inspired"
instead. Every claim that the patent has expired that this document checked was
unsourced.

**Shadow Robot has not gone into administration.** The claim circulates.
Companies House records company number 03308007 as Active, with share allotments
filed in June 2025, May 2026 and June 2026, and no insolvency, liquidation or
strike-off filing of any kind.

### 5.7 One older market event worth not repeating

Soft Robotics Inc divested its gripper business to the Schmalz Group on 6 August
2024, and its mGrip line is now a Schmalz product. That is already recorded in
[the gripper document's soft gripper
section](../07_gripping/02_grippers-and-hardware.md#5-soft-and-compliant-grippers)
and nothing has changed since. It is repeated here only because comparison
articles listing Soft Robotics as a gripper vendor are still circulating, and they
are more than two years out of date.

## 6. Tactile and force sensing

This moved further and faster than anything else in this document, and it moved
mostly by getting cheap rather than by getting better.

### 6.1 A six-axis force-torque sensor now has a published price

A force-torque sensor at the wrist measures the six numbers that describe how the
tool is being pushed and twisted: three forces and three torques.
[The gripper document explains what you do with
one](../07_gripping/02_grippers-and-hardware.md#81-force-and-torque-at-the-wrist)
and records the Robotiq FT 300-S specification in detail.

Before, no manufacturer published a price. ATI, Robotiq, Schunk and Bota all sold
through integrators, and the figures in circulation were reseller quotes.

What changed is that [UFACTORY's shop lists a six-axis force-torque sensor at
$3,000](https://www.ufactory.cc/xarm-collaborative-robot/), in the same public
product feed as its arms. That is not a price cut, because there was no published
price before it to cut. It is the appearance of a number where there had been
none, which for a buyer is the more useful event.

How it was achieved is the channel rather than the technology. A vendor selling
arms from a web shop has to price the accessories in the same shop.

Why it matters is budgeting. A wrist force-torque sensor is the standard way to
give a position-controlled arm a sense of contact, and until now you could not
find out what one cost without a sales conversation.

What it still cannot do is tell you how good it is. UFACTORY publishes the price
and not the noise floor, and the noise floor is the number that decides what the
sensor can detect. The Robotiq figures in the gripper document — a 0.1 N signal
noise and a recommended 1 N contact-detection threshold — remain the only
complete published set.

Status: Shipping.

### 6.2 Touch sensing became something you buy for tens of dollars

Before, a tactile sensor was a research instrument. GelSight Mini at $510, with
replacement gels at $57 and a stated gel life of 1,000 coin presses, was
[the only tactile product in the whole gripper document with a published
price](../07_gripping/02_grippers-and-hardware.md#82-tactile-sensing-at-the-contact).
Everything else was a paper with a repository attached.

What changed is a manufacturing ecosystem around the open research designs. Read
the table as: what the thing is, what it costs, and where the price comes from.

| Product | What it is | Published price |
| --- | --- | --- |
| [eFlesh magnetometer board](https://shop.wowrobo.com/) | the recommended sensing board for the open eFlesh magnetic-skin project | $25 for one, $180 for ten |
| [WowSkin](https://shop.wowrobo.com/) | a manufactured magnetic skin built on the open AnySkin and ReSkin designs, with mounts for SO-100, SO-101 and Koch | $48 for the skin alone, $128 with the structural part |
| [OSMO tactile glove](https://shop.wowrobo.com/) | an open tactile glove with twelve three-axis sensors across the fingertips and palm, for recording human demonstrations | $100 for the skin, $780 for the complete set |
| [Robotiq TSF-85](https://robotiq.com/tactile-sensor-fingertips) | 28 taxels at 1000 Hz on a production gripper fingertip, [section 5.2](#52-tactile-fingertips-became-a-gripper-accessory) | none published |

How it was achieved is the same mechanism as the arm kits in
[section 3.2](#32-the-real-change-was-the-kit-ecosystem). AnySkin and ReSkin are
open designs from academic groups, published with permissive licences — AnySkin's
repository is MIT — and a manufacturer read the files and made them properly.
Magnetic skin is also intrinsically cheap: it is a magnetised elastomer over a
board of magnetometers, and magnetometers are a commodity part made in the
billions for phones.

Why it matters is that touch stopped being a project. A $48 skin on a $122 arm is
a tactile robot for under two hundred dollars, and that was not possible in 2024
at any price a person would pay from their own pocket.

What it still cannot do is any of the things the gripper document already lists.
No manufacturer in this category publishes a slip-detection latency, which is the
number you would most want. Magnetic skins drift with temperature and need
re-zeroing. Gels wear out. And there is still no standard for tactile data, so a
policy trained on one sensor does not transfer to another — which is exactly the
gap that the tactile foundation models described in
[the mechanism document](../10_one-arm-training/05_what-is-changing.md#tactile-foundation-models)
are trying to close, and they have not closed it yet.

Status: Shipping, all of them.

### 6.3 Tactile sensing arrived inside the hands

The other route to touch is to buy a hand that already has it, and that became
possible in the period.

The specifications the vendors publish, for the hands in
[section 4.3](#43-the-hands-separately-purchasable-at-last-but-not-from-everyone)
and [section 5.3](#53-multi-finger-hands-became-genuinely-affordable). Read this
as: whose hand, how much of it senses touch, and what the smallest force it
resolves is.

| Hand | Tactile coverage | Smallest force stated |
| --- | --- | --- |
| [AgiBot OmniHand O12](https://www.agibot.com/products/OmniHand_O12) | "150+ tactile points", three-axis at the fingertips, one-axis in the palm | 0.01 N |
| [Unitree Dex3-1](https://www.unitree.com/Dex3-1) | 33 tactile sensors across nine pressure arrays | 10 g, about 0.1 N |
| [Unitree Dex5-1P](https://www.unitree.com/Dex5-1) | 94 tactile sensors per hand, on the P version only | not published |
| [PaXini DexH13](https://mall.paxini.com/product/dex/66f27ea530cd11a8e9d1d5ff) | 1,140 tactile units across 3,420 channels, plus an 8-megapixel palm camera | not published |
| [Figure 03](https://www.figure.ai/news/introducing-figure-03) | fingertips, plus an embedded palm camera in each hand | 3 g, about 0.03 N |

The pattern worth extracting is that the sensitivity figures are now well below
what a wrist force-torque sensor can see. The gripper document's Robotiq FT 300-S
recommends a 1 N threshold for detecting contact. A fingertip claiming 0.01 N is
two orders of magnitude finer, and it is finer because it is in the right place:
a wrist sensor reads the whole load below it, and a fingertip reads only the
contact.

What it still cannot do is come without the hand. Every entry in that table is a
sensor you get by buying a complete hand, most of them at four or five figures,
and the tactile version is often a separate more expensive product — AgiBot
charges $940 for the option and Unitree's base Dex5-1 has no tactile sensing at
all. If you want touch on a gripper you already own, the answer is section 6.2 or
the Robotiq fingertips, not a hand.

## 7. On-robot compute

What you put on the robot changed more in this period than the robot did, and it
changed in a direction nobody predicted in 2024.

### 7.1 The one verified price cut: Orin Nano Super, December 2024

Before, the entry-level NVIDIA Jetson developer kit was the Orin Nano at $499, a
figure NVIDIA published in March 2023. The step up was [the Jetson AGX Orin
Developer Kit at
$1,999](https://developer.nvidia.com/blog/develop-ai-powered-robots-smart-vision-systems-and-more-with-nvidia-jetson-orin-nano-developer-kit/),
upgraded to 64 GB of memory at the same price.

What changed is that on 17 December 2024 NVIDIA published, in its own words, a
"New reduced price of $249, down from $499" for the Orin Nano, renamed the
[Orin Nano
Super](https://developer.nvidia.com/blog/nvidia-jetson-orin-nano-developer-kit-gets-a-super-boost/).
At the same moment the compute figure went from 40 to 67 sparse INT8 TOPS — that
is trillions of eight-bit integer operations per second, counted with the
sparsity optimisation applied — and memory bandwidth went from 65 to 102 GB/s,
with a new 25 W power mode.

How it was achieved is the part that makes this the most interesting event in the
section. **It was a software update.** The silicon did not change. Existing Orin
Nano owners received the performance increase for nothing, by updating JetPack and
selecting the new power mode. NVIDIA had been shipping the hardware below its
capability and then unlocked it.

Why it matters is that it halved the price of the standard entry-level robot
computer, and it is the only NVIDIA Jetson price reduction this document could
verify from NVIDIA's own publication.

What it still cannot do is tell you today's price. NVIDIA prints no prices on any
current Jetson product page, and both of the stores its own "Shop Now" buttons
point at — its marketplace and its Jetson store — failed to respond to repeated
automated requests. Every dollar figure in this section is therefore a launch
price published in an NVIDIA blog post on a stated date, not a street price today.
Given section 7.4, the difference may be large.

Status: Shipping.

### 7.2 Jetson Thor, and how to read its headline number

Before, the top of the Jetson range was the AGX Orin at up to 275 sparse INT8
TOPS in a 15 to 60 W envelope.

What changed is [Jetson AGX
Thor](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-thor/),
announced on 25 August 2025 with a developer kit price of $3,499. The T5000
module carries a 2560-core Blackwell graphics processor, a 14-core Arm
Neoverse-V3AE processor, 128 GB of 256-bit LPDDR5X memory at 273 GB/s, and a
power envelope of 40 to 130 W. NVIDIA states its compute as 2070 TFLOPS, and the
footnote on its own specification table gives the condition: FP4, sparse,
measured at 130 W. The smaller T4000 gives 1200 FP4 TFLOPS with 64 GB. NVIDIA
guarantees availability of the T5000 through August 2035.

How to read the headline is where care is needed, and this is the single most
misquoted number in robotics hardware. NVIDIA claims Thor delivers "7.5× the
performance and 3.5× the energy efficiency of NVIDIA AGX Orin". That comparison
puts Thor's FP4 sparse figure against Orin's INT8 sparse figure. Those are
different number formats. FP4 is a four-bit floating-point format and INT8 is an
eight-bit integer one, and an operation in one is not an operation in the other.
NVIDIA publishes no dense FP4 figure for Thor at all. The 7.5× is a real
engineering achievement and it is not a like-for-like multiple, and anyone
repeating it without saying so is passing on a marketing number.

The same care applies one level down. NVIDIA publishes both sparse and dense
figures for the Orin family, and every headline in circulation is the sparse one:
the AGX Orin 64 GB is 275 TOPS sparse and 85 TOPS dense on its tensor cores, and
the Orin Nano Super is 67 sparse against 33 dense. If you are sizing a model
against a TOPS figure, the dense number is the one that describes what you will
get. NVIDIA's own Jetson Orin page currently carries a contradiction on this
point, listing the AGX Orin 32 GB at both 241 and 200 sparse TOPS in different
tables; a June 2026 NVIDIA blog post resolves it in favour of 241, describing a
20 per cent boost above the original specification.

Why Thor matters is memory rather than arithmetic. 128 GB of unified memory on a
robot means a model that previously needed a workstation now fits.

What it still cannot do is feed itself. 273 GB/s against 2070 TFLOPS makes
large-language-model decoding bandwidth-bound rather than compute-bound, and
NVIDIA's own MLPerf submission of 16 September 2026 shows what that means in
practice: 52.33 output tokens per second on a 27-billion-parameter model at
NVFP4, with a median time to first token of 247 ms, on a single developer kit at
maximum power. It also cannot run on a battery comfortably. Its floor is 40 W
against the Orin Nano's 7 W, and on a mobile robot that is a design constraint
rather than a detail.

Status: Shipping. NVIDIA stated on 15 July 2026 that "Developers can begin
building today using the Jetson AGX Thor developer kit available through channel
partners".

### 7.3 What was announced and has not arrived

Two Jetson products are Announced with a date and neither is buyable.

The **T3000 and T2000** modules, [announced on 15 July
2026](https://blogs.nvidia.com/blog/jetson-thor-robotics-edge-ai-agent/), give
865 and 400 FP4 TFLOPS, with the T3000 at 32 GB and described as roughly half the
size and power of the T5000. NVIDIA states they "are scheduled to become
available in Q1 2027" and publishes no price. NVIDIA's stated reason for the
smaller parts is worth quoting because it is unusually candid: "Migrating to T3000
helps reduce costs amid high memory prices."

The **Jetson Orin Nano 2**, [announced on 25 August
2026](https://nvidianews.nvidia.com/news/nvidia-announces-jetson-orin-nano-2-robotics-computer-to-redefine-entry-level-edge-ai),
gives "78 trillion operations per second of AI compute, 8GB of memory and an
8-core Arm CPU", is claimed to deliver "2x the inference performance of Jetson
Orin Nano Super", and to consume "40% less power to deliver the same performance
as its predecessor" in 15 W mode. It is expected in the first half of 2027 and no
price is published. NVIDIA does not state the precision behind the 78 figure, so
this document does not either.

The instructive detail is the arithmetic. Going from 67 to 78 is a factor of 1.16,
and NVIDIA claims twice the inference performance. The gain comes from memory
bandwidth and improved tensor cores, not from arithmetic throughput. NVIDIA's own
product is the clearest available demonstration that TOPS is the wrong number to
choose a robot computer by.

### 7.4 The actual story of 2026 is memory prices

This is the thing a reader planning a budget most needs to know, and it has
nothing to do with robots.

Before, a Raspberry Pi 5 with 8 GB of memory cost $80 and was the default cheap
robot computer.

What changed is that memory prices rose sharply, and Raspberry Pi documented it
in its own words across several dated posts: "an unprecedented rise in the cost of
LPDDR4 memory, thanks to competition for memory fab capacity from the AI
infrastructure roll-out", and "a seven-fold increase over the last year in the
price of the LPDDR4 DRAM used on Raspberry Pi 4 and 5". The published prices moved
accordingly: the 2 GB Pi 5 from $50 to $65, the 4 GB from $60 to $110, the 8 GB
from $80 to $175, and the 16 GB from $120 to $305. Raspberry Pi introduced a new
[1 GB Pi 5 at
$45](https://www.raspberrypi.com/news/1gb-raspberry-pi-5-now-available-at-45-and-memory-driven-price-rises/)
to have anything cheap left in the range, and calls the pressure "painful but
ultimately temporary".

How it happened is the data-centre build-out competing for the same fabrication
capacity. It is the clearest case in this document of the robot market being a
passenger in somebody else's economy.

Why it matters is immediate and practical. **Any board price you remember from
before 2026 may be wrong by a factor of two.** An 8 GB Pi 5 more than doubled. The
same force is visible on the NVIDIA side in the sentence quoted in section 7.3.

What it still cannot do is be predicted. Raspberry Pi says temporary and does not
say when.

Status: current, and the reason to re-check every price before you buy.

### 7.5 The alternatives, and what each publishes

Read this table as: the part, what its maker claims for compute and in what
precision, and whether a price is published anywhere by the maker.

| Part | Vendor's compute figure | Published price | Status |
| --- | --- | --- | --- |
| [Raspberry Pi AI HAT+ 2](https://www.raspberrypi.com/news/introducing-the-raspberry-pi-ai-hat-plus-2-generative-ai-on-raspberry-pi-5/), Hailo-10H | "40 TOPS (INT4)", 20 TOPS at INT8, 8 GB on board | $200 | Shipping |
| Raspberry Pi AI HAT+, Hailo-8 and 8L | 26 and 13 TOPS, **precision not stated by Hailo** | "from $70" | Shipping |
| Raspberry Pi AI Camera | **no compute figure published** | $70 | Shipping |
| [Qualcomm Dragonwing IQ-9075](https://www.qualcomm.com/internet-of-things/products/iq9-series/iq-9075) | "100 Dense TOPS dedicated NPU", INT8 stated | none | Shipping |
| [Qualcomm Dragonwing IQ10](https://www.qualcomm.com/internet-of-things/products/iq10-series) | "up to 700 TOPS (350 dense TOPS at INT8 precision)" | none | Announced, availability from September 2026 |
| [Texas Instruments TDA4VM](https://www.ti.com/product/TDA4VM) | "up to 8 TOPS (8b) at 1.0GHz" | $113.413 at one to ninety-nine units | Shipping |
| Texas Instruments AM69A | "Total of 32 TOPS" | $377.444 at one to ninety-nine units | Shipping |
| [Rockchip RK3588](https://www.rock-chips.com/a/en/products/RK35_Series/2022/0926/1660.html) | "6.0 TOPs NPU", **precision not tied to the figure** | none from Rockchip | Shipping |
| [Google Coral Edge TPU](https://developers.google.com/coral/guides/roadmap) | "4 TOPS (int8); 2 TOPS per watt" | $59.99 for the USB accelerator | effectively withdrawn, see below |

Five things in that table are worth more than the numbers.

**Texas Instruments is the only vendor here that publishes a price for a chip.**
It is also the only one that has shipped nothing new: the whole TDA4 and AM6xA
family is on a 16 nanometre process and its pitch is functional safety and
backward compatibility rather than throughput. For a robot that has to be
certified, that is the point rather than a weakness.

**Qualcomm's 700 TOPS headline is half that at INT8 dense**, and Qualcomm says so
on its own page. This is the same reading problem as Thor's 7.5×, and Qualcomm
handles it more honestly by printing both numbers side by side.

**Qualcomm's most consequential move is not silicon.** It [announced on 23
September 2026 that it will acquire PickNik
Robotics](https://www.qualcomm.com/news/releases/2026/09/qualcomm-to-acquire-picknik-to-advance-the-future-of-open-roboti),
the stewards of MoveIt, stating that MoveIt 1 and MoveIt 2 will "remain open,
community-driven, and supported across third-party hardware platforms". A chip
vendor buying the motion-planning framework is a bid for the layer above the
silicon.

**Hailo does not state the precision behind its two best-known figures.** The 26
TOPS of the Hailo-8 and the 13 of the Hailo-8L are printed without a format,
while the Hailo-10H's "40 TOPS of INT4" is qualified. At matched INT8 precision
the newer Hailo-10H is 20 TOPS against the older Hailo-8's 26, which is why
Raspberry Pi describes the new board's vision performance as "broadly equivalent"
to its predecessor. The gain is the 8 GB of memory, not the throughput.

**Google Coral is gone without being discontinued.** There is no end-of-life
notice, and the boilerplate that would carry one has not been used. But coral.ai
now redirects wholesale to a Google developer page, the legacy news page's most
recent dated release is from July 2021, and the successor — an open-source
RISC-V design licensed Apache-2.0 — targets a ten-milliwatt wearable envelope,
which is a direction away from robots. Google's own words are that it is "an
evolution of Google's edge AI strategy, rather than a direct replacement for
Coral". If you have Coral in a design, plan to move.

Two fetching notes belong here because they affect how much of the above could be
checked. Raspberry Pi and Hailo both return HTTP 403 to an automated request
with browser headers, which is a bot block rather than a dead page, so their
figures were read through a renderer instead. And NVIDIA's news host returns HTTP
200 for any path at all, so a 200 there proves nothing on its own.

### 7.6 What a robot actually runs, as against what it could

The gap between the top of the range and the deployed fleet is wider than the
announcements suggest, and NVIDIA's own customer list shows it. [Its June 2026
account of named
deployments](https://blogs.nvidia.com/blog/jetson-agentic-ai-physical-world/)
puts Zipline's delivery drones and SandStar's vending machines on Orin NX, and
describes Hexagon and Solomon as *integrating* Thor into humanoids. An earlier
NVIDIA post describes Caterpillar's assistant on Thor as "in development". Even
[the Unitree G1](https://www.unitree.com/g1), at $13,500, specifies only an
"8-core high-performance CPU" in its base form, with Orin appearing as an option
on the EDU version.

The pattern is that shipping robots run Orin NX and Orin Nano, while Thor is in
humanoids, demonstrations and development. That is the honest difference between
2024 and 2026: the top of the range moved a long way and the deployed fleet did
not move much at all.

One independent benchmark is worth reporting because it reframes the question,
with its disclosure attached. Open Navigation, the company behind the Nav2
navigation stack, published a robotics workload benchmark in July 2026 comparing
Jetson Thor, Jetson AGX Orin and an AMD Strix Halo part on a simulated forklift
with nine sensors. Open Navigation states that the work was a collaboration with
AMD and that the benchmark was executed independently, and you should weigh the
results with that in mind. Its finding is that Thor's misses in the control loop
came from its Arm cores saturating on trajectory planning — work that cannot be
moved to the graphics processor — and that the AGX Orin ran at 93.6 per cent mean
processor utilisation and completed three of ten missions. Whether or not the
comparison favours the sponsor, the mechanism it identifies is checkable and
matters: on a modern ROS 2 workload the binding constraint is single-core
processor performance for planning, not graphics-processor TOPS.

### 7.7 Real-time, which did not arrive on Jetson

A robot that must guarantee a control loop needs a real-time operating system,
meaning one that bounds how long a task can be delayed rather than merely making
delays rare.

Before, real-time Linux meant applying the PREEMPT_RT patch set to the kernel
yourself, and it had been an out-of-tree patch for about two decades.

What changed is that [PREEMPT_RT was merged into mainline Linux in version 6.12,
released on 17 November 2024](https://kernelnewbies.org/Linux_6.12). What remains
out of tree is now tiny: the current supplementary patch is a few hundred lines
and touches nothing in the scheduler, the locking code or the timer core.

What did not change is Jetson. NVIDIA's own documentation still says that
"Real-Time Kernel support is provided with Developer-Preview quality" for the
Thor and Orin modules, and has said so since release 35.1. JetPack 7 ships a 6.8
kernel, which predates the 6.12 merge, so Jetson's real-time support is still a
patched out-of-tree kernel rather than mainline PREEMPT_RT. Building the display
drivers under it requires setting a flag that overrides NVIDIA's own check for
the presence of PREEMPT_RT, which tells you how well tested the combination is.

Why this matters is that the compute story and the control story point in
opposite directions. You can now put a 2070-teraflop computer on a robot, and the
part of the software that has to hit a deadline every millisecond is running on a
kernel its vendor labels a developer preview.

One more scheduling fact belongs here because it will bite anyone pairing the
two. The current ROS 2 long-term release is **Lyrical Luth**, released on 22 May
2026 and supported to May 2031. Its tier-one platform is Ubuntu 26.04, and
JetPack 7 ships Ubuntu 24.04, which Lyrical supports only as a source build. In
practice Jazzy, supported to May 2029, remains the distribution that pairs with a
Jetson, and this document could not reconcile that with NVIDIA's own claim of
Lyrical support on Ubuntu 24.04 in Isaac ROS 5.0.

## 8. The category that did not exist: teleoperation hardware

This section is here because nothing in the brief for this document asked for it,
and it is the largest genuinely new hardware category of the period.

Before, if you wanted to collect demonstrations for imitation learning you built
your own leader device. GELLO — a printed replica of the robot's kinematics with
encoders instead of motors — was a paper and a repository, and everyone who
wanted one made one.

What changed is that the leader arm became a product, from several directions at
once, in a single eighteen-month stretch.

Enactic sells the [OpenArm KER](https://github.com/enactic/openarm_ker), which it
calls a Kinematic Equivalent Replica: a lightweight leader arm that matches the
follower's joint layout. WowRobo lists it at $2,599, and the individual encoder
unit at $49. The software is Apache-2.0; as with the arm itself, the hardware
files sit in a separate repository with a separate licence, so check it.

Franka Robotics lists Franka GELLO and GELLO Duo on
[its own product page](https://franka.de/), labelled as prototypes. A major
industrial arm vendor productising an academic teleoperation rig is a reasonable
marker for when a research idea has finished arriving.

Elephant Robotics sells the [myController
S570](https://shop.elephantrobotics.com/), described as a portable exoskeleton
robot controller for data capture, at $1,300 on its own store. AgileX lists a
Universal Master Arm and the PIKA PRO handheld data-collection device on
[its store](https://global.agilex.ai/), both without a published price. Trossen
sells a teleoperation product called Glide with a Cockpit operator station, also
without a published price.

Hugging Face went in the opposite direction and removed the robot from the loop
entirely. [Grabette](https://huggingface.co/blog/grabette), published on 21 July
2026, is "a handheld gripper instrumented with everything needed to reconstruct a
manipulation demonstration" — two cameras with distinct jobs, an inertial
measurement unit and a gripper — with a bill of materials of about €490, and a
companion motorised gripper called Gripette at about €120. It writes "a standard
LeRobot dataset on the Hugging Face Hub", storing demonstrations as a
camera-local six-degree-of-freedom pose plus a gripper state. Its ancestor is
UMI, the universal manipulation interface.

There is also an industrial version of the same idea. Universal Robots' news
centre records, on 16 March 2026, a joint launch with Scale AI of the UR AI
Trainer, described as generating training data in dedicated training cells. A
training cell is a room full of hardware whose only product is demonstrations.

How this category came about is the data constraint that
[the mechanism document](../10_one-arm-training/05_what-is-changing.md#2-the-five-forces-driving-2026)
puts first among its five forces. If demonstrations are the binding constraint on
what a learned policy can do, then a device that makes demonstrations cheaper is
worth more than a better arm, and the market responded to that literally.

Why it matters, and this is the practical point for a reader with a small budget,
is that a €490 handheld recorder lets you collect a dataset before you own a
robot at all. That inverts the usual order of a robot-learning project.

What it still cannot do is close the gap between a human hand and a robot. A
handheld recorder captures a trajectory a person made with human wrists and human
compliance, and the robot that has to reproduce it has neither. Whether policies
trained this way transfer is an open question, not a settled one, and
[the learned-methods document](../10_one-arm-training/03_learned-methods.md) is
the place to read about it.

Status: OpenArm KER, Grabette, Gripette and the myController S570 are Shipping.
Franka GELLO and GELLO Duo are Demonstrated, labelled prototypes by the vendor.
The UR AI Trainer is Announced with a date.

## 9. What did not change

A document about change earns its keep by being specific about what stayed
still, because those are the numbers you can plan around.

**Mid-range industrial arm prices did not move.** The UFACTORY xArm 6 was
$8,399 in June 2024, $8,399 in January 2025 and $8,399 in September 2026. That is
the only mid-range arm with a public price series, and it is flat.

**The major cobot vendors still publish nothing.** Universal Robots, Franka
Robotics, Kinova, Doosan, Techman, Elite Robots, JAKA and Dobot were all fetched
in September 2026 and none of them publishes a price for any product. This has
not changed in years and there is no sign of it changing.

**Research hands from the established vendors are still quote-only.** Shadow
Robot and Wonik Allegro publish no price, exactly as recorded in
[the gripper document](../07_gripping/02_grippers-and-hardware.md#6-multi-finger-hands).

**Precision at the cheap end is still a millimetre.** Trossen's WidowX AI states
1 mm of repeatability. The industrial arms state 0.1 mm. That factor of ten did
not close, and it is the number that decides whether a demonstration can be
replayed.

**Dexterous hands still cannot carry anything.** Every hand with more than three
fingers in this document carries between 500 g and 5 kg, and the strong ones are
the least dexterous. This has been true for a decade.

**The bottom of the cheap-arm market stopped falling.** The SO-101 bill of
materials fell about five per cent in twenty-three months and the servos are now
most of the cost, so there is no further saving of the kind that produced the
hundred-dollar arm in the first place.

**Suction, magnetic and tool-changer hardware produced no event worth
recording.** Every figure in
[the corresponding sections of the gripper
document](../07_gripping/02_grippers-and-hardware.md#3-suction) is current, and
nothing in the period displaced a Schmalz cup or an ATI changer.

**Nobody publishes a slip-detection latency.** The gripper document noted this
gap and it is still a gap. A 1000 Hz sampling rate, which Robotiq's new tactile
fingertips also quote, bounds the latency from below and is not the same number.

## 10. How to check an announcement yourself

The research for this document produced a small set of habits that are worth
more than any individual number in it, because they will still work next year.

**Find out which channel the vendor sells through, because it tells you whether a
price exists.** A vendor with a web shop publishes everything; a vendor with a
quote form publishes nothing. There is no middle case, and knowing which one you
are dealing with saves an hour.

**Try the shop's own data feed before reading the page.** Many robot vendors run
their stores on standard e-commerce platforms that expose a machine-readable
product list. Appending `/products.json` to a Shopify storefront, or
`/wp-json/wc/store/products` to a WooCommerce one, returned the complete priced
catalogue for four of the vendors in this document in a single request, including
products that the human-readable pages do not list together. This is public
information the vendor chose to publish; it is simply published in a second
place.

**Use dated snapshots for historical prices.** The Internet Archive holds the
same product page from previous years, and the difference between two snapshots
is the only honest way to say whether something got cheaper. Every "it used to
cost" claim in this document has a snapshot behind it, and the snapshot has a
date printed on it.

**For open hardware, find the repository holding the design files and read its
own licence file.** Do not read the badge on the main repository. OpenArm is the
worked example: the software is Apache-2.0 and the CAD is CERN-OHL-S-2.0, which
is strongly reciprocal and obliges you to publish your own design files if you
distribute a product based on it. The two repositories belong to the same
organisation and their licences impose completely different obligations.

**Check that a degrees-of-freedom figure carries its qualifier.** Actuated,
total, and joint count are three different numbers. A vendor that writes "20
degrees of freedom (16 active + 4)" is being honest. A secondary source that
writes "20 degrees of freedom" has removed the information.

**Check that a payload figure carries its conditions.** OpenArm's "4.1 kg (held
for 1 minute in the worst posture)" is a usable number. A bare "4 kg" is not, for
[the reasons the gripper document
gives](../07_gripping/02_grippers-and-hardware.md#1-how-to-read-a-gripper-datasheet):
payload is a static figure and acceleration spends it.

**Treat an unreachable page as unverified, not as confirmed.** Several vendors in
this document serve nothing to an automated request, either by blocking it or by
rendering everything in the browser. That is a reason to say a number could not
be obtained. It is never a reason to take the number from somebody who resells
the product.

**Ask what maturity label the announcement deserves.** A deposit is not a
delivery, a video is not a product, and a page with no date on it is not a plan.
Applying the four labels from [section 1.1](#11-the-four-maturity-labels) to an
announcement takes about a minute and it is the single most useful minute in this
entire subject.

---

Back to the rest of the frontier area, or across to
[what is changing in robot manipulation](../10_one-arm-training/05_what-is-changing.md)
for why hardware moves the way it does. For what any of this hardware can
actually hold, see
[grippers and the hardware around them](../07_gripping/02_grippers-and-hardware.md).
